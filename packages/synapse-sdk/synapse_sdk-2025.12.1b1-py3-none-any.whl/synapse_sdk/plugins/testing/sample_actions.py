"""Sample actions for integration testing."""

import time

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction


# Sample parameter/result models
class Step1Params(BaseModel):
    dataset_id: int


class Step1Result(BaseModel):
    dataset_id: int
    dataset_path: str


class Step2Params(BaseModel):
    dataset_path: str


class Step2Result(BaseModel):
    dataset_path: str
    converted_path: str


class Step3Params(BaseModel):
    converted_path: str
    epochs: int = 5


class Step3Result(BaseModel):
    model_path: str
    metrics: dict[str, float]


# Sample actions
class DownloadAction(BaseAction[Step1Params]):
    """Simulates downloading a dataset."""

    action_name = 'download'
    params_model = Step1Params
    result_model = Step1Result

    def execute(self) -> Step1Result:
        self.ctx.logger.info(f'Downloading dataset {self.params.dataset_id}...')
        time.sleep(1)  # Simulate work
        return Step1Result(
            dataset_id=self.params.dataset_id,
            dataset_path=f'/tmp/datasets/{self.params.dataset_id}',
        )


class ConvertAction(BaseAction[Step2Params]):
    """Simulates converting a dataset."""

    action_name = 'convert'
    params_model = Step2Params
    result_model = Step2Result

    def execute(self) -> Step2Result:
        self.ctx.logger.info(f'Converting dataset at {self.params.dataset_path}...')
        time.sleep(1)  # Simulate work
        return Step2Result(
            dataset_path=self.params.dataset_path,
            converted_path=f'{self.params.dataset_path}/yolo',
        )


class TrainAction(BaseAction[Step3Params]):
    """Simulates training a model."""

    action_name = 'train'
    params_model = Step3Params
    result_model = Step3Result

    def execute(self) -> Step3Result:
        self.ctx.logger.info(f'Training on {self.params.converted_path} for {self.params.epochs} epochs...')
        time.sleep(2)  # Simulate work
        return Step3Result(
            model_path='/tmp/models/best.pt',
            metrics={'mAP50': 0.85, 'mAP50-95': 0.72},
        )


__all__ = [
    'Step1Params',
    'Step1Result',
    'Step2Params',
    'Step2Result',
    'Step3Params',
    'Step3Result',
    'DownloadAction',
    'ConvertAction',
    'TrainAction',
]
