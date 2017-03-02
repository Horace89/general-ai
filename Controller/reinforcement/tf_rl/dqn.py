from __future__ import print_function

from reinforcement.tf_rl.rl_implementations.neural_q_learner import NeuralQLearner
import tensorflow as tf
import tensorflow.contrib.layers as tf_layers
from utils.activations import get_activation_tf
import numpy as np
import time
from reinforcement.environment import Environment
import utils.miscellaneous
import constants
import os
import json
from reinforcement.abstract_reinforcement import AbstractReinforcement

STD = 0.01
MAX_EPISODES = 1000000
MAX_STEPS = 50000


class DQN(AbstractReinforcement):
    """
    Represents a deep q-network reinforcement learning (epsilon-greedy policy).
    """

    def __init__(self, game, parameters, q_network_parameters, optimizer_parameters):

        self.parameters = parameters
        self.q_network_parameters = q_network_parameters
        self.optimizer_params = optimizer_parameters

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
        # Hidden fully connected layers
        x = None
        for i, dim in enumerate(self.q_network_parameters["hidden_layers"]):
            x = tf_layers.fully_connected(inputs=input,
                                          num_outputs=dim,
                                          activation_fn=get_activation_tf(self.q_network_parameters["activation"]),
                                          weights_initializer=tf.random_normal_initializer(mean=0, stddev=STD),
                                          scope="fully_connected_{}".format(i))

        # Output logits
        logits = tf_layers.fully_connected(inputs=x,
                                           num_outputs=self.num_actions,
                                           activation_fn=None,
                                           weights_initializer=tf.random_normal_initializer(mean=0, stddev=STD),
                                           scope="output_layer")

        return logits

    def init_directories(self, dir_name=None):
        dir = constants.loc + "/logs/" + self.game + "/dqn"
        current = time.localtime()
        t_string = "{}-{}-{}_{}-{}-{}".format(str(current.tm_year).zfill(2), str(current.tm_mon).zfill(2),
                                              str(current.tm_mday).zfill(2), str(current.tm_hour).zfill(2),
                                              str(current.tm_min).zfill(2), str(current.tm_sec).zfill(2))
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
        start = time.time()
        tmp = time.time()
        line = ""
        for i_episode in range(MAX_EPISODES):

            self.env = Environment(game_class=self.game_class,
                                   seed=np.random.randint(0, 2 ** 30),
                                   observations_count=self.state_size,
                                   actions_in_phases=self.actions_count,
                                   discrete=True)

            # initialize
            state = self.env.state
            total_rewards = 0
            self.negative_reward = 0

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
                    line = "Episode: {}, Steps: {}, Score: {}, Current exploration rate: {}".format(i_episode, t + 1,
                                                                                                    info,
                                                                                                    self.q_learner.exploration)
                    data.append(line)
                    break

            if (t + 1) == MAX_STEPS:
                print("Maximum number of steps within single game exceeded. ")

            if i_episode % 100 == 0:
                self.test_and_save(data, start, i_episode)

            if time.time() - tmp > 1:
                print(line)
                tmp = time.time()

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
                                   actions_in_phases=self.actions_count,
                                   discrete=True)
            # initialize
            state = self.env.reset()

            for t in range(MAX_STEPS):
                action = self.q_learner.eGreedyAction(state[np.newaxis, :])
                next_state, reward, done, info = self.env.step(self.convert_to_sequence(action))
                state = next_state

                if done:
                    avg_test_score += info
                    break

        avg_test_score /= n_iterations
        return avg_test_score