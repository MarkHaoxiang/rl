# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import annotations

import importlib.util

import torch
from tensordict import TensorDict, TensorDictBase
from torchrl.data.replay_buffers.samplers import SamplerWithoutReplacement

from torchrl.data.tensor_specs import Categorical, Composite, Unbounded
from torchrl.envs.common import EnvBase
from torchrl.envs.transforms import Compose, DoubleToFloat, RenameTransform
from torchrl.envs.utils import _classproperty

_has_sklearn = importlib.util.find_spec("sklearn", None) is not None


def _make_composite_from_td(td):
    # custom function to convert a tensordict in a similar spec structure
    # of unbounded values.
    composite = Composite(
        {
            key: _make_composite_from_td(tensor)
            if isinstance(tensor, TensorDictBase)
            else Unbounded(dtype=tensor.dtype, device=tensor.device, shape=tensor.shape)
            if tensor.dtype in (torch.float16, torch.float32, torch.float64)
            else Unbounded(dtype=tensor.dtype, device=tensor.device, shape=tensor.shape)
            for key, tensor in td.items()
        },
        shape=td.shape,
    )
    return composite


class OpenMLEnv(EnvBase):
    """An environment interface to OpenML data to be used in bandits contexts.

    Doc: https://www.openml.org/search?type=data

    Scikit-learn interface: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_openml.html

    Args:
        dataset_name (str): the following datasets are supported:
            ``"adult_num"``, ``"adult_onehot"``, ``"mushroom_num"``, ``"mushroom_onehot"``,
            ``"covertype"``, ``"shuttle"`` and ``"magic"``.
        device (torch.device or compatible, optional): the device where the input
            and output data is to be expected. Defaults to ``"cpu"``.
        batch_size (torch.Size or compatible, optional): the batch size of the environment,
            ie. the number of elements samples and returned when a :meth:`reset` is
            called. Defaults to an empty batch size, ie. one element is sampled
            at a time.

    Attributes:
        available_envs (List[str]): list of envs to be built by this class.

    Examples:
        >>> env = OpenMLEnv("adult_onehot", batch_size=[2, 3])
        >>> print(env.reset())
        TensorDict(
            fields={
                done: Tensor(shape=torch.Size([2, 3, 1]), device=cpu, dtype=torch.bool, is_shared=False),
                observation: Tensor(shape=torch.Size([2, 3, 106]), device=cpu, dtype=torch.float32, is_shared=False),
                reward: Tensor(shape=torch.Size([2, 3, 1]), device=cpu, dtype=torch.float32, is_shared=False),
                y: Tensor(shape=torch.Size([2, 3]), device=cpu, dtype=torch.int64, is_shared=False)},
            batch_size=torch.Size([2, 3]),
            device=cpu,
            is_shared=False)

    """

    @_classproperty
    def available_envs(cls):
        if not _has_sklearn:
            return []
        return [
            "adult_num",
            "adult_onehot",
            "mushroom_num",
            "mushroom_onehot",
            "covertype",
            "shuttle",
            "magic",
        ]

    def __init__(self, dataset_name, device="cpu", batch_size=None):
        from torchrl.data.datasets.openml import OpenMLExperienceReplay

        if batch_size is None:
            batch_size = torch.Size([])
        else:
            batch_size = torch.Size(batch_size)
        self.dataset_name = dataset_name
        self._data = OpenMLExperienceReplay(
            dataset_name,
            batch_size=batch_size.numel(),
            sampler=SamplerWithoutReplacement(drop_last=True),
            transform=Compose(
                RenameTransform(["X"], ["observation"]),
                DoubleToFloat(["observation"]),
            ),
        )
        super().__init__(device=device, batch_size=batch_size)
        self.observation_spec = _make_composite_from_td(
            self._data[: self.batch_size.numel()]
            .reshape(self.batch_size)
            .exclude("index")
        )
        self.action_spec = Categorical(
            self._data.max_outcome_val + 1, shape=self.batch_size, device=self.device
        )
        self.reward_spec = Unbounded(shape=(*self.batch_size, 1))

    def _reset(self, tensordict):
        data = self._data.sample()
        data = data.exclude("index")
        data = data.reshape(self.batch_size).to(self.device)
        return data

    def _step(
        self,
        tensordict: TensorDictBase,
    ) -> TensorDictBase:
        action = tensordict.get("action")
        y = tensordict.get("y", None)
        if y is None:
            raise KeyError(
                "did not find the 'y' key in the input tensordict. "
                "Make sure you call env.step() on a tensordict that results "
                "from env.reset()."
            )

        if action.shape != y.shape:
            raise RuntimeError(
                f"Action and outcome shape differ: {action.shape} vs {y.shape}."
            )
        reward = (action == tensordict["y"]).float().unsqueeze(-1)
        done = torch.ones_like(reward, dtype=torch.bool)
        td = TensorDict(
            {
                "done": done,
                "reward": reward,
                **tensordict.select(*self.observation_spec.keys()),
            },
            self.batch_size,
            device=self.device,
        )
        return td

    def _set_seed(self, seed: int | None) -> None:
        self.rng = torch.random.manual_seed(seed)
