# -*-coding:utf-8-*-

import random

import numpy as np

from Hmm import Hmm


class Robot(Hmm):
    _OBSERVATIONS_COUNT = 16

    def get_size(self):
        return self.size

    def set_size(self, size):
        self.size = size

    def get_obstacle_rate(self):
        # Not implemented
        return self.obstacle_rate

    def set_obstacle_rate(self, obstacle_rate):
        # Not implemented
        self.obstacle_rate = obstacle_rate

    def get_map(self):
        return self.map_mat

    def generate_map(self):
        self.map_mat = np.zeros((self.size, self.size), dtype=int)
        for x in range(0, self.size):
            for y in range(0, self.size):
                self.map_mat[x][y] = random.sample([0, 0, 0, 0, 1], 1)[0]

    def print_map(self):
        for x in range(0, self.size):
            print(self.map_mat[x])

    def get_error(self):
        return self.error

    def set_error(self, error):
        self.error = error

    def state_to_coordinates(self, state):
        valid_states = self.map_mat.size - np.count_nonzero(self.map_mat)
        if state > valid_states:
            raise Exception
        state_countdown = state
        for x in range(self.map_mat.shape[0]):
            for y in range(self.map_mat.shape[1]):
                if self.map_mat[x][y] == 0:
                    if state_countdown < 1:
                        return x, y
                    else:
                        state_countdown -= 1

    def make_a_mat(self):
        ''' Calculate the state transition probability matrix

        .. warning:: Generate map before using it
        '''
        valid_states = self.map_mat.size - np.count_nonzero(self.map_mat)
        shape = (valid_states, valid_states)
        a_mat = np.zeros((shape[0], shape[1]))
        for state1 in range(valid_states):
            for state2 in range(valid_states):
                a_mat[state1][state2] = self._get_estate_transition_probability(state1, state2)
        self.a_mat = a_mat

    def make_pi_v(self):
        ''' Calculate the initial state probability vector

        .. warning:: Generate map before using it
        '''
        valid_states = self.map_mat.size - np.count_nonzero(self.map_mat)
        pi_v = np.zeros((valid_states, 1))
        pi_v += 1 / valid_states
        self.pi_v = pi_v

    def make_b_mat(self):
        valid_states = self.map_mat.size - np.count_nonzero(self.map_mat)
        shape = (valid_states, 16)  # From 1111(0000), to 2222(1111), NSWE
        b_mat = np.zeros((shape[0], shape[1]))
        for state in range(valid_states):
            coords_state = self.state_to_coordinates(state)
            obstacles = 1111
            if coords_state[0] - 1 < 0 or self.map_mat[coords_state[0] - 1][coords_state[1]] == 1:
                obstacles += 1000
            if coords_state[0] + 1 >= self.size or self.map_mat[coords_state[0] + 1][coords_state[1]] == 1:
                obstacles += 100
            if coords_state[1] - 1 < 0 or self.map_mat[coords_state[0]][coords_state[1] - 1] == 1:
                obstacles += 10
            if coords_state[1] + 1 >= self.size or self.map_mat[coords_state[0]][coords_state[1] + 1] == 1:
                obstacles += 1
            obstacles = str(obstacles)
            observation = 0
            for n in range(2):
                for s in range(2):
                    for w in range(2):
                        for e in range(2):
                            obstacle_check = n * 1000 + s * 100 + w * 10 + e + 1111
                            obstacle_check = str(obstacle_check)
                            probability = 1.0
                            for c in range(len(obstacle_check)):
                                if obstacle_check[c] == obstacles[c]:
                                    probability *= (1 - self.get_error())
                                else:
                                    probability *= self.get_error()
                            b_mat[state][observation] = probability
                            observation += 1
        self.b_mat = b_mat

    def print_b_mat(self):
        valid_states = self.map_mat.size - np.count_nonzero(self.map_mat)
        np.set_printoptions(threshold=np.inf)
        for x in range(valid_states):
            print(self.b_mat[x])

    def _get_estate_transition_probability(self, state, prev_state):
        ''' Calculate transition probability between states.
        Needs map matrix with paths (self.map_mat)
        Args:
            state (int) Target state identifier
            prev_state (int) Start state identifier
        Returns:
            (float) Probability of transition between start to target states
        '''
        state_pos = self.state_to_coordinates(state)
        prev_state_pos = self.state_to_coordinates(prev_state)

        valid_adjacents = 4
        transition_found = False

        if state_pos != prev_state_pos and (state_pos[0] == prev_state_pos[0] or state_pos[1] == prev_state_pos[1]):
            # N
            if prev_state_pos[0] <= 0 or self.map_mat[prev_state_pos[0] - 1, prev_state_pos[1]] == 1:
                valid_adjacents -= 1
            elif state_pos[0] == prev_state_pos[0] - 1:
                transition_found = True
            # S
            if prev_state_pos[0] >= self.map_mat.shape[0] - 1 or self.map_mat[
                        prev_state_pos[0] + 1, prev_state_pos[1]] == 1:
                valid_adjacents -= 1
            elif not transition_found and state_pos[0] == prev_state_pos[0] + 1:
                transition_found = True
            # W
            if prev_state_pos[1] <= 0 or self.map_mat[prev_state_pos[0], prev_state_pos[1] - 1] == 1:
                valid_adjacents -= 1
            elif not transition_found and state_pos[1] == prev_state_pos[1] - 1:
                transition_found = True
            # E
            if prev_state_pos[1] >= self.map_mat.shape[1] - 1 or self.map_mat[
                prev_state_pos[0], prev_state_pos[1] + 1] == 1:
                valid_adjacents -= 1
            elif not transition_found and state_pos[1] == prev_state_pos[1] + 1:
                transition_found = True
            if transition_found == True:
                return 1 / valid_adjacents
        return 0

    def generate_sample(self, size):
        ''' Generates a sequence of states and its observations for the present system

        :param size: Length of string of states
        :return: Tuple with string of states and observations

        .. warning:: size must be greater than 0
            Make A, B and Pi before using it
        '''
        if size is None or size < 1:
            raise ValueError("size must be greater than 0")
        valid_states = self.pi_v.shape[0]
        sample_s = np.empty(size, int)
        sample_o = np.empty(size, int)
        np.put(sample_s, 0, np.random.choice(
            valid_states,
            1,
            p=np.transpose(self.pi_v[:, 0])))
        np.put(sample_o, 0, np.random.choice(
            self._OBSERVATIONS_COUNT,
            1,
            p=np.transpose(self.b_mat[sample_s[0]])))
        for i in range(1, size):
            np.put(sample_s, i, np.random.choice(
                valid_states,
                1,
                p=np.transpose(self.a_mat[:, sample_s[i - 1]])))
            np.put(sample_o, i, np.random.choice(
                self._OBSERVATIONS_COUNT,
                1,
                p=np.transpose(self.b_mat[sample_s[i]])))
        return sample_s, sample_o

    # observations must give values between 0 (no obstacles) and 15 (NWSE obstacles)
    def forward(self, time, observations):
        # Exceptions for senseless arguments
        if observations is None:
            raise Exception
        if time is None or time < 0:
            raise Exception
        if len(observations) < time:
            raise Exception

        # Generate matrix if they aren't built yet
        if self.a_mat is None:
            self.make_a_mat
        if self.pi_v is None:
            self.make_pi_v
        if self.b_mat is None:
            self.b_mat

        # Initialization
        valid_states = self.map_mat.size - np.count_nonzero(self.map_mat)
        shape = (valid_states, time)
        forward_mat = np.zeros((shape[0], shape[1]))

        # Step 1
        for s in range(valid_states):
            forward_mat[s][0] = self.b_mat[s][observations[0]] * self.pi_v[s]

        # Next steps
        if time >= 1:
            for t in range(1, time):
                for s in range(valid_states):
                    accumulated = 0.0
                    for ss in range(valid_states):
                        accumulated += (self.a_mat[s][ss] * forward_mat[ss][t - 1])
                    forward_mat[s][t] = self.b_mat[s][observations[t - 1]] * accumulated

        return forward_mat
