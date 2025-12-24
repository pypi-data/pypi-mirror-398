import unittest

from stageflow.core.context import Context
from stageflow.core.event import InputSpec
from stageflow.core.node import TerminalNode
from stageflow.core.pipeline import Pipeline
from stageflow.core.session import Session
from stageflow.core.stage import BaseStage


def _make_pipeline():
    end = TerminalNode(id="end", type="terminal")
    return Pipeline(entry="end", nodes=[end])


class StageWaitInputTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_and_finish_wait_input_success(self):
        session = Session(id="stage1", pipeline=_make_pipeline(), context=Context())

        class WaitStage(BaseStage):
            allowed_inputs = [InputSpec(type="user", payload_schema={"id": int})]

            async def run(self):
                return None

        stage = WaitStage(stage_id="s1", config={}, arguments={}, outputs={}, session=session)
        fut = stage.start_wait_input("user")
        await session.input("user", {"id": 10})

        result = await stage.finish_wait_input("user", fut, timeout=1)
        self.assertEqual(result["payload"]["id"], 10)

    async def test_finish_wait_input_validates_payload(self):
        session = Session(id="stage2", pipeline=_make_pipeline(), context=Context())

        class WaitStage(BaseStage):
            allowed_inputs = [InputSpec(type="user", payload_schema={"id": int})]

            async def run(self):
                return None

        stage = WaitStage(stage_id="s1", config={}, arguments={}, outputs={}, session=session)
        fut = stage.start_wait_input("user")
        await session.input("user", {"id": "bad"})

        with self.assertRaises(ValueError):
            await stage.finish_wait_input("user", fut, timeout=1)

    async def test_start_wait_input_rejects_disallowed_type(self):
        session = Session(id="stage3", pipeline=_make_pipeline(), context=Context())

        class LimitedStage(BaseStage):
            allowed_inputs = [InputSpec(type="only")]

            async def run(self):
                return None

        stage = LimitedStage(stage_id="s1", config={}, arguments={}, outputs={}, session=session)
        with self.assertRaises(ValueError):
            stage.start_wait_input("other")


if __name__ == "__main__":
    unittest.main()
