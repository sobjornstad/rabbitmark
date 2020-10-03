from behave import *
import re

import rabbitmark.cli

@given(u'the RabbitMark test database is configured')
def step_impl(context):
    # Currently we don't have to do this, as it's hard-coded...
    pass


@when(u'we run the command "{command}"')
def step_impl(context, command):
    command_seq = command.split(' ')  # TODO: Fails for quoted args
    result = rabbitmark.cli.call(command_seq)
    context.result_lines = result.split('\n')


@then(u'we get one search result')
def step_impl(context):
    assert len(context.result_lines) == 3, len(context.result_lines)


@then(u'the result is named "{name}".')
def step_impl(context, name):
    print(context.result_lines[2])
    assert re.match(f'^[\\s0-9]*\\s*{re.escape(name)}', context.result_lines[2])
