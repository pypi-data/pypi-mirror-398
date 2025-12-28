# Copyright 2022 Christopher Wickens. All rights reserved.

import logging

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.pool
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (
    relationship,
)
from sqlalchemy.orm.exc import NoResultFound  # noqa
from sqlalchemy.sql import sqltypes as st
from sqlalchemy.sql.functions import func

import otree.common
from otree.channels import utils as channel_utils
from otree.common2 import json_dumps
from otree.database import ExtraModel, dbq
from otree.lookup import get_page_lookup
from otree.models import Participant

logger = logging.getLogger(__name__)


class BaseTrial(ExtraModel):
    # We should have a class for this because:
    # - makes it easier to enforce correctness
    # - we may need to add stuff to it in the future.
    # - less code to loop and create trials in the regular case
    # - if someone forgets to assign queue_positions, then all queue positions will be None
    #   and it will skip right past the trials page, which will be confusing.
    # - if doing infinite iteration, the trials will not all be created at the same time.
    #   therefore, it's hard to know what the previous queue_position was.
    #   need to store it somewhere, which is a pain.

    __abstract__ = True

    # can't use autoincrement=True because that only has an effect
    # if the field is part of the primary key.
    queue_position = Column(st.Integer)
    page_name = Column(st.String)

    @declared_attr
    def player_id(cls):
        app_name = cls.get_folder_name()
        # needs to be nullable so re-grouping can happen
        return Column(st.Integer, ForeignKey(f'{app_name}_player.id'), nullable=True)

    @declared_attr
    def player(cls):
        # back_populates=f'{cls.__name__}_set'
        return relationship(
            f'{cls.__module__}.Player',
        )

    @classmethod
    def create(cls, **kwargs):
        if 'queue_position' not in kwargs:
            global _incrementing_queue_position
            if _incrementing_queue_position is None:
                _incrementing_queue_position = (
                    dbq(func.max(cls.queue_position)).scalar() or 1
                )
            _incrementing_queue_position += 1
            kwargs['queue_position'] = _incrementing_queue_position
        page_class = kwargs.pop('page', None)
        if isinstance(page_class, type):
            kwargs['page_name'] = page_class.__name__
        return super().create(**kwargs)


# queue position doesn't need to always contain the global max, but it must consistently increment
# for a given player, even between server restarts (because you might create trials on the fly).
# it's OK if 1 app passes queue_position explicitly, and another app auto-increments.
# because those queue positions will never get compared to each other.
_incrementing_queue_position = None


async def trial_payload_function(participant_code, page_name, msg):

    try:
        participant = Participant.objects_get(code=participant_code)
    except NoResultFound:
        logger.warning(f'Participant not found: {participant_code}')
        return

    def send_error():
        """need to put it in a function, otherwise we get a warning
        that the coroutine wasn't awaited."""
        return _send_back(
            participant_code,
            participant._index_in_pages,
            dict(type='error'),
        )

    lookup = get_page_lookup(participant._session_code, participant._index_in_pages)
    app_name = lookup.app_name
    models_module = otree.common.get_models_module(app_name)
    PageClass = lookup.page_class
    if page_name != PageClass.__name__:
        logger.warning(
            f'Ignoring message from {participant_code} because '
            f'they are on page {PageClass.__name__}, not {page_name}.'
        )
        await send_error()

    player = models_module.Player.objects_get(
        round_number=lookup.round_number, participant=participant
    )
    Trial = PageClass.trial_model
    page_name = PageClass.__name__
    trial = get_current_trial(Trial, player, page_name)
    msg_type = msg['type']
    is_page_load = msg_type == 'load'
    resp = dict(is_page_load=is_page_load, type=msg_type)
    if trial and msg_type == 'response':
        if trial.id != msg['trial_id']:
            await send_error()
            msg = (
                "Trials: server and client are out of sync. "
                "Check if there were any errors earlier."
            )
            raise Exception(msg)
        response: dict = msg['response']
        if hasattr(PageClass, 'evaluate_trial'):
            try:
                feedback = PageClass.evaluate_trial(trial, response)
            except Exception:
                await send_error()
                raise
        else:
            server_fields = set(PageClass.trial_response_fields)
            client_fields = response.keys()
            server_only = server_fields - client_fields
            if server_only:
                await send_error()
                msg = (
                    "The following fields are in trial_response_fields, "
                    f"but were not received from sendTrialResponse: {server_only}. "
                    "If this key was indeed sent, make sure its value is non-null."
                )
                raise Exception(msg)
            client_only = client_fields - server_fields
            if client_only:
                await send_error()
                msg = (
                    "The following fields were sent from the sendTrialResponse, "
                    f"but are not in trial_response_fields: {client_only}"
                )
                raise Exception(msg)
            try:
                # need to do it this way rather than having an overridable evaluate_trial,
                # because it's a static method, so has no access to trial_response_fields.
                # we don't enforce non-null, because some trial fields may be optional or N/A,
                # e.g. reaction time if the user didn't react.
                for attr in PageClass.trial_response_fields:
                    setattr(trial, attr, response[attr])
            except Exception:
                await send_error()
                raise
            trial.queue_position = None
            feedback = {}
        resp.update(feedback=feedback)
        trial = get_current_trial(Trial, player, page_name)
    if trial:
        resp.update(trial=encode_trial(trial, PageClass.trial_stimulus_fields))
    else:
        resp.update(trial=None, completed_all_trials=True)
    progress = get_progress(Trial, player, page_name)
    progress.update(PageClass.trial_page_vars(player))
    resp.update(progress=progress)
    await _send_back(
        participant.code,
        participant._index_in_pages,
        resp,
    )


def encode_trial(trial, fields):
    fields = fields.copy()
    if 'id' not in fields:
        fields.append('id')
    return {attr: getattr(trial, attr) for attr in fields}


def get_all_trials(Trial, player, page_name: str):
    return Trial.objects_filter(_filter_by_page(Trial, page_name), player=player)


def _filter_by_page(Trial, page_name):
    return sqlalchemy.or_(Trial.page_name == page_name, Trial.page_name == None)


def get_progress(Trial, player, page_name: str) -> dict:
    trials = get_all_trials(Trial, player, page_name)
    total = trials.count()
    remaining = trials.filter(Trial.queue_position != None).count()

    return dict(
        numTrials=total,
        numTrialsRemaining=remaining,
        numTrialsCompleted=total - remaining,
    )


def get_current_trial(Trial, player, page_name):
    return (
        get_all_trials(Trial, player, page_name)
        .filter(Trial.queue_position != None)
        .order_by('queue_position')
        .first()
    )


async def _send_back(pcode, page_index, resp):
    '''separate function for easier patching'''

    group_name = channel_utils.trial_group(pcode, page_index)
    await channel_utils.group_send(
        group=group_name,
        data=resp,
    )
