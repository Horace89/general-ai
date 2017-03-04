from __future__ import print_function

import json
import os
import time

import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as tf_layers

import constants
import utils.miscellaneous
from reinforcement.abstract_reinforcement import AbstractReinforcement
from reinforcement.dqn.neural_q_learner import NeuralQLearner
from reinforcement.environment import Environment
from utils.activations import get_activation_tf

STD = 0.01
MAX_EPISODES = 1000000
MAX_STEPS = 50000


class DQN(AbstractReinforcement):
    """
    Represents a deep q-network reinforcement learning (epsilon-greedy policy).
    """

    def __init__(self, game, parameters, q_network_parameters, optimizer_parameters, test_every=10):
        """
        Initializes a new instance of DQN reinforcement learning model.
        :param game: Game to play.
        :param parameters: DQNParameters instance.
        :param q_network_parameters: Dictionary; Q-network parameters.
        :param optimizer_parameters: Dictionary; Optimizer parameters.
        :param test_every: Testing every n-th episode.
        """

        self.parameters = parameters
        self.q_network_parameters = q_network_parameters
        self.optimizer_params = optimizer_parameters
        self.test_every = test_every

        self.checkpoint_name = "dqn.ckpt"
        lr = self.optimizer_params["learning_rate"]
        if self.optimizer_params["name"] == "rmsprop":
            d = self.optimizer_params["decay"]
            m = self.optimizer_params["momentum"]
            self.optimizer = tf.train.RMSPropOptimizer(learning_rate=lr, decay=d, momentum=m)
        if self.optimizer_params["name"] == "adam":
            self.optimizer = tf.train.AdamOptimizer(learning_rate=lr)

        self.game = game
        self.game_config = utils.miscellaneous.get_game_config(game)
        self.game_class = utils.miscellaneous.get_game_class(game)
        self.state_size = self.game_config["input_sizes"][0]

        self.actions_count = self.game_config["output_sizes"]
        self.actions_count_sum = sum(self.actions_count)
        self.init_directories()

        self.sess = tf.Session(config=tf.ConfigProto(inter_op_parallelism_threads=16,
                                                     intra_op_parallelism_threads=16,
                                                     allow_soft_placement=True))

        self.writer = tf.summary.FileWriter(logdir=self.logdir,
                                            graph=self.sess.graph,
                                            flush_secs=10)

        self.num_actions = self.actions_count_sum

        self.q_learner = NeuralQLearner(self.sess,
                                        self.optimizer,
                                        self.q_network,
                                        self.state_size,
                                        self.num_actions,
                                        summary_writer=self.writer,
                                        init_exp=self.parameters.init_exp,
                                        final_exp=self.parameters.final_exp,
                                        batch_size=self.parameters.batch_size,
                                        anneal_steps=self.parameters.anneal_steps,
                                        replay_buffer_size=self.parameters.replay_buffer_size,
                                        target_update_rate=self.parameters.target_update_rate,
                                        store_replay_every=self.parameters.store_replay_every,
                                        discount_factor=self.parameters.discount_factor,
                                        reg_param=self.parameters.reg_param,
                                        max_gradient=self.parameters.max_gradient,
                                        double_q_learning=self.parameters.double_q_learning)

        self.agent = self.q_learner

    def q_network(self, input):
        """
        Defines Q-Network. Tensorflow stuff.
        :param input: Input state
        :return: Logits.
        """

        # Hidden fully connected layers
        x = None
        for i, dim in enumerate(self.q_network_parameters["hidden_layers"]):
            x = tf_layers.fully_connected(inputs=input,
                                          num_outputs=dim,
                                          activation_fn=get_activation_tf(self.q_network_parameters["activation"]),
                                          weights_initializer=tf.random_normal_initializer(mean=0, stddev=STD),
                                          scope="fully_connected_{}".format(i))
            if self.q_network_parameters["dropout"] != None:
                x = tf_layers.dropout(x, keep_prob=self.q_network_parameters["dropout"])

        # Output logits
        logits = tf_layers.fully_connected(inputs=x,
                                           num_outputs=self.num_actions,
                                           activation_fn=None,
                                           weights_initializer=tf.random_normal_initializer(mean=0, stddev=STD),
                                           scope="output_layer")

        return logits

    def init_directories(self, dir_name=None):
        """
        Initializes directories used for logging.
        """
        self.test_logbook_data.append("Testing every {} episodes".format(self.test_every))

        dir = constants.loc + "/logs/" + self.game + "/dqn"
        t_string = utils.miscellaneous.get_pretty_time()

        self.logdir = dir + "/logs_" + t_string
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)

        with open(os.path.join(self.logdir, "metadata.json"), "w") as f:
            data = {}
            data["model_name"] = "DQN"
            data["game"] = self.game
            data["q_network"] = self.q_network_parameters
            data["parameters"] = self.parameters.to_dictionary()
            data["optimizer_parameters"] = self.optimizer_params
            f.write(json.dumps(data))

    def run(self):
        data = []
        data.append("Episode Steps Score Exploration_rate Time")
        start = time.time()
        tmp = time.time()
        line = ""
        for i_episode in range(MAX_EPISODES):

            self.env = Environment(game_class=self.game_class,
                                   seed=np.random.randint(0, 2 ** 30),
                                   observations_count=self.state_size,
                                   actions_in_phases=self.actions_count)

            # initialize
            state = self.env.state
            total_rewards = 0
            self.negative_reward = 0
            game_start = time.time()

            for t in range(MAX_STEPS):
                action = self.q_learner.eGreedyAction(state[np.newaxis, :])
                next_state, reward, done, info = self.env.step(self.convert_to_sequence(action))

                total_rewards += reward
                if reward < 0:
                    self.negative_reward += 1
                self.q_learner.storeExperience(state, action, reward, next_state, done)

                self.q_learner.updateModel()
                state = next_state
                if done:
                    game_time = time.time() - game_start
                    line = "Episode: {}, Steps: {}, Score: {}, Current exploration rate: {}, Time: {}".format(
                        i_episode, t + 1, info, self.q_learner.exploration, game_time)
                    data.append("{} {} {} {}".format(i_episode, t + 1, info, self.q_learner.exploration, game_time))
                    break

            if (t + 1) == MAX_STEPS:
                print("Maximum number of steps within single game exceeded. ")

            if time.time() - tmp > 1:
                print(line)
                tmp = time.time()

            if i_episode % self.test_every == 0:
                self.test_and_save(data, start, i_episode)

            self.q_learner.measure_summaries(i_episode, info, t + 1, self.negative_reward)

    def convert_to_sequence(self, action):
        """
        From specified action, creates a list of n outputs, onehot encoding.
        """
        result = np.zeros(self.num_actions)
        result[action] = 1
        return result

    def test(self, n_iterations):
        avg_test_score = 0

        for i_episode in range(n_iterations):

            self.env = Environment(game_class=self.game_class,
                                   seed=np.random.randint(0, 2 ** 30),
                                   observations_count=self.state_size,
                                   actions_in_phases=self.actions_count)
            # initialize
            state = self.env.state

            for t in range(MAX_STEPS):
                action = self.q_learner.eGreedyAction(state[np.newaxis, :])
                next_state, reward, done, info = self.env.step(self.convert_to_sequence(action))
                state = next_state

                if done:
                    avg_test_score += info
                    break

        avg_test_score /= n_iterations
        return avg_test_score