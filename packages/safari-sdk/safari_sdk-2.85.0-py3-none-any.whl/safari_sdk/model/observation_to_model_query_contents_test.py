# Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import json

import numpy as np

from absl.testing import absltest
from safari_sdk.model import constants
from safari_sdk.model import observation_to_model_query_contents


class ObservationToModelQueryContentsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.task_instruction_key = 'instruction'
    self.string_obs_key = 'string_obs'
    self.proprio_obs_key = 'proprio'
    self.image_obs_key = 'image'

  def test_observation_serialization(self):
    observation = {
        self.task_instruction_key: np.array('do the task'),
        self.string_obs_key: np.array('some string'),
        self.proprio_obs_key: np.array([1.0, 2.0]),
        self.image_obs_key: np.zeros((64, 64, 3), dtype=np.uint8),
    }

    contents = (
        observation_to_model_query_contents.observation_to_model_query_contents(
            observation=observation,
            string_observations_keys=('instruction', 'string_obs'),
            task_instruction_key='instruction',
            proprioceptive_observation_keys=('proprio',),
            image_observation_keys=('image',),
        )
    )

    encoded_obs = json.loads(contents[-1])
    images = contents[:-1]

    self.assertLen(images, 1)
    np.testing.assert_array_equal(images[0], observation[self.image_obs_key])

    self.assertEqual(
        encoded_obs['task_instruction'],
        np.array_str(observation[self.task_instruction_key]),
    )
    self.assertEqual(
        encoded_obs[self.string_obs_key],
        np.array_str(observation[self.string_obs_key]),
    )
    self.assertEqual(
        encoded_obs[self.proprio_obs_key],
        observation[self.proprio_obs_key].tolist(),
    )
    self.assertEqual(
        encoded_obs[f'{constants.IMAGE_ENCODED_OBS_PREFIX}image'], 0
    )

  def test_multiple_images(self):
    image_obs_key2 = 'image2'
    observation = {
        self.task_instruction_key: np.array('do the task'),
        self.proprio_obs_key: np.array([1.0, 2.0]),
        self.image_obs_key: np.zeros((64, 64, 3), dtype=np.uint8),
        image_obs_key2: np.ones((64, 64, 3), dtype=np.uint8),
    }

    contents = (
        observation_to_model_query_contents.observation_to_model_query_contents(
            observation=observation,
            task_instruction_key='instruction',
            proprioceptive_observation_keys=('proprio',),
            string_observations_keys=[self.task_instruction_key],
            image_observation_keys=[self.image_obs_key, image_obs_key2],
        )
    )

    encoded_obs = json.loads(contents[-1])
    images = contents[:-1]

    self.assertLen(images, 2)
    np.testing.assert_array_equal(images[0], observation[self.image_obs_key])
    np.testing.assert_array_equal(images[1], observation[image_obs_key2])
    self.assertEqual(
        encoded_obs[
            f'{constants.IMAGE_ENCODED_OBS_PREFIX}{self.image_obs_key}'
        ],
        0,
    )
    self.assertEqual(
        encoded_obs[f'{constants.IMAGE_ENCODED_OBS_PREFIX}{image_obs_key2}'], 1
    )

  def test_proprio_with_batch_dimension(self):
    observation = {
        self.proprio_obs_key: np.array([[1.0, 2.0]]),
    }

    contents = (
        observation_to_model_query_contents.observation_to_model_query_contents(
            observation=observation,
            task_instruction_key='instruction',
            proprioceptive_observation_keys=('proprio',),
            string_observations_keys=[],
            image_observation_keys=[],
        )
    )
    encoded_obs = json.loads(contents[-1])

    self.assertEqual(encoded_obs[self.proprio_obs_key], [1.0, 2.0])

  def test_invalid_proprio_dims_raises_error(self):
    observation = {
        self.proprio_obs_key: np.zeros((1, 1, 1)),
    }
    with self.assertRaisesRegex(
        ValueError, 'Observation proprio has 3 dimensions, but should be 1.'
    ):

      observation_to_model_query_contents.observation_to_model_query_contents(
          observation=observation,
          task_instruction_key='instruction',
          proprioceptive_observation_keys=('proprio',),
          string_observations_keys=[],
          image_observation_keys=[],
      )

  def test_image_with_batch_dimension(self):
    observation = {
        self.image_obs_key: np.zeros((1, 64, 64, 3), dtype=np.uint8),
    }

    contents = (
        observation_to_model_query_contents.observation_to_model_query_contents(
            observation=observation,
            string_observations_keys=[],
            proprioceptive_observation_keys=[],
            task_instruction_key='instruction',
            image_observation_keys=('image',),
        )
    )

    images = contents[:-1]
    self.assertEqual(images[0].shape, (64, 64, 3))

  def test_invalid_image_dims_raises_error(self):
    observation = {
        self.image_obs_key: np.zeros((64, 64), dtype=np.uint8),
    }
    with self.assertRaisesRegex(
        ValueError, 'Image image has 2 dimensions, but should be 3.'
    ):

      observation_to_model_query_contents.observation_to_model_query_contents(
          observation=observation,
          string_observations_keys=[],
          proprioceptive_observation_keys=[],
          task_instruction_key='instruction',
          image_observation_keys=('image',),
      )

  def test_image_as_bytes(self):
    image_bytes = b'some_image_bytes'
    observation = {
        self.image_obs_key: image_bytes,
    }

    contents = (
        observation_to_model_query_contents.observation_to_model_query_contents(
            observation=observation,
            string_observations_keys=[],
            task_instruction_key='instruction',
            image_observation_keys=('image',),
            proprioceptive_observation_keys=[],
        )
    )
    images = contents[:-1]

    self.assertLen(images, 1)
    self.assertEqual(images[0], image_bytes)


if __name__ == '__main__':
  absltest.main()
