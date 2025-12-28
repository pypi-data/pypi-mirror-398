import gym
import numpy as np

from sklearn.preprocessing import KBinsDiscretizer
import time, math, random
from typing import Tuple

def init():
    env = gym.make('CartPole-v1', render_mode="human")

    n_episodes = 1
    env_vis = []

    for i_episode in range(n_episodes):
        observation = env.reset()
        for t in range(100):
            env_vis.append(env.render())
            action = env.action_space.sample()
            observation, reward, done,trun, info = env.step(action)
            # if done:
            #     print("Episode finished at t{}".format(t+1))
            #     break



def policy_logic(env,obs,**kw):
    return 1 if obs[2] > 0 else 0

def policy_random(env,obs,**kw):
    return env.action_space.sample()

def policy_random_para(env,obs,**kw):
    theta = kw['theta']
    return 0 if np.matmul(theta,obs) < 0 else 1


def experiment(policy, n_episodes, rewards_max):
    rewards=np.empty(shape=(n_episodes))
    env = gym.make('CartPole-v1')


    for i in range(n_episodes):
        obs,_ = env.reset()
        done = False
        episode_reward = 0
        theta = np.random.rand(4)*2 - 1

        while not done:
            # env.render()
            action = policy(env,obs,theta=theta)
            # obs 推车位置，速度，杆与竖直方向的夹角，角速度
            # print(env.step(action))
            obs, reward, done, info,_ = env.step(action)
            # print("obs",obs)
            episode_reward += reward
            if episode_reward > rewards_max:
                break
            rewards[i]=episode_reward
    print('Policy:{}, Min reward:{}, Max reward:{}'
    .format(policy.__name__,
            min(rewards),
            max(rewards)))
            
        


def policy_random_train(theta,obs):
  return 0 if np.matmul(theta,obs) < 0 else 1

def episode(env,policy, rewards_max,theta):
    obs,_ = env.reset()
    done = False
    episode_reward = 0
    while not done:
        # env.render()
        action = policy(theta,obs)
        obs, reward, done, _,info = env.step(action)
        episode_reward += reward
        if episode_reward > rewards_max:
            break
    return episode_reward

def train(policy, n_episodes, rewards_max):

    env = gym.make('CartPole-v1')
    theta_best = np.empty(shape=[4])
    reward_best = 0

    for i in range(n_episodes):
        theta = np.random.rand(4) * 2 - 1

        reward_episode=episode(env,policy,rewards_max, theta)
        if reward_episode > reward_best:
            reward_best = reward_episode
            theta_best = theta.copy()
    return reward_best,theta_best

def experiment_train(policy, n_episodes, rewards_max, theta=None):
    rewards=np.empty(shape=[n_episodes])
    env = gym.make('CartPole-v1')

    for i in range(n_episodes):
        rewards[i]=episode(env,policy,rewards_max,theta)
            #print("Episode finished at t{}".format(reward))
    print('Policy:{}, Min reward:{}, Max reward:{}, Average reward:{}'
            .format(policy.__name__,
                    np.min(rewards),
                    np.max(rewards),
                    np.mean(rewards)))

# qlearning
    

# discretize the value to a state space
def discretize(val,bounds,n_states):
    discrete_val = 0
    if val <= bounds[0]:
        discrete_val = 0
    elif val >= bounds[1]:
        discrete_val = n_states-1
    else:
        discrete_val = int(round( (n_states-1) * 
                                    ((val-bounds[0])/
                                    (bounds[1]-bounds[0])) ))
    return discrete_val

def discretize_state(vals,s_bounds,n_s):
    discrete_vals = []
    for i in range(len(n_s)):
        discrete_vals.append(discretize(vals[i],s_bounds[i],n_s[i]))
    return np.array(discrete_vals,dtype=np.int)

def policy_q_table(state, env, q_table, explore_rate=0.2):
    # Exploration strategy - Select a random action
    if np.random.random() < explore_rate:
        action = env.action_space.sample()
    # Exploitation strategy - Select the action with the highest q
    else:
        action = np.argmax(q_table[tuple(state)])
    return action


def experiment_q_learning(policy, n_episodes, r_max=200,t_max=200):
    # 相关参数
    learning_rate = 0.8
    discount_rate = 0.9
    explore_rate = 0.2
    n_episodes = 1000

    env = gym.make('CartPole-v1')
    n_a = env.action_space.n
    # number of discrete states for each observation dimension
    n_s = [10,10,10,10]   # position, velocity, angle, angular velocity
    s_bounds = list(zip(env.observation_space.low,env.observation_space.high))
    s_bounds[1] = [-1.0,1.0]
    s_bounds[3] = [-1.0,1.0]
    # create a Q-Table of shape (10,10,10,10, 2) representing S X A -> R
    q_table = np.zeros(shape = np.append(n_s,n_a)) # (10,10,10,10,2)

    rewards=np.empty(shape=[n_episodes])
    for i in range(n_episodes):
        # val = episode(env, policy, r_max, t_max)
        obs = env.reset()
        state_prev = discretize_state(obs,s_bounds,n_s)
        episode_reward = 0
        done = False
        t = 0
        # 选择操作并观察下一个状态
        action = policy(state_prev, env, q_table, explore_rate)
        obs, reward, done, info = env.step(action)
        state_new = discretize_state(obs,s_bounds,n_s)
        # 更新Q表
        best_q = np.amax(q_table[tuple(state_new)])
        bellman_q = reward + discount_rate * best_q
        indices = tuple(np.append(state_prev,action))
        q_table[indices] += learning_rate*( bellman_q - q_table[indices])

        state_prev = state_new
        episode_reward += reward
        
        print("best_q", best_q)
        rewards[i] = episode_reward 
    print('Policy:{}, Min reward:{}, Max reward:{}, Average reward:{}'
        .format(policy.__name__,
                np.min(rewards),
                np.max(rewards),
                np.mean(rewards)))


def experiment_q_learning2(policy, n_episodes):
    env = gym.make('CartPole-v1')
    n_bins = ( 6 , 12 )
    lower_bounds = [ env.observation_space.low[2], -math.radians(50) ]
    upper_bounds = [ env.observation_space.high[2], math.radians(50) ]

    def discretizer( _ , __ , angle, pole_velocity ) -> Tuple[int,...]:
        """Convert continues state intro a discrete state"""
        est = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='uniform')
        est.fit([lower_bounds, upper_bounds ])
        return tuple(map(int,est.transform([[angle, pole_velocity]])[0]))

    Q_table = np.zeros(n_bins + (env.action_space.n,))

    def policy( state : tuple ):
        """Choosing action based on epsilon-greedy policy"""
        return np.argmax(Q_table[state])

    def new_Q_value( reward : float ,  new_state : tuple , discount_factor=1 ) -> float:
        """Temperal diffrence for updating Q-value of state-action pair"""
        future_optimal_value = np.max(Q_table[new_state])
        learned_value = reward + discount_factor * future_optimal_value
        return learned_value

    # Adaptive learning of Learning Rate
    def learning_rate(n : int , min_rate=0.01 ) -> float  :
        """Decaying learning rate"""
        return max(min_rate, min(1.0, 1.0 - math.log10((n + 1) / 25)))
    
    def exploration_rate(n : int, min_rate= 0.1 ) -> float :
        """Decaying exploration rate"""
        return max(min_rate, min(1, 1.0 - math.log10((n  + 1) / 25)))
    n_episodes = 10000 
    for e in range(n_episodes):
        
        # Siscretize state into buckets
        current_state, done = discretizer(*env.reset()), False
        
        while done==False:
            
            # policy action 
            action = policy(current_state) # exploit
            
            # insert random action
            if np.random.random() < exploration_rate(e) : 
                action = env.action_space.sample() # explore 
            
            # increment enviroment
            obs, reward, done, _ = env.step(action)
            new_state = discretizer(*obs)
            
            # Update Q-Table
            lr = learning_rate(e)
            print("reward",reward)
            learnt_value = new_Q_value(reward , new_state )
            old_value = Q_table[current_state][action]
            Q_table[current_state][action] = (1-lr)*old_value + lr*learnt_value
            
            current_state = new_state
            
            # Render the cartpole environment
            # env.render()

if __name__ == "__main__":
    init()
    # experiment(policy_random, 100, 10000)
    # experiment(policy_logic, 100, 10000)
    # experiment(policy_random_para, 100, 10000)
    # reward,theta = train(policy_random_train, 100, 10000)
    # print('trained theta: {}, rewards: {}'.format(theta,reward))
    # experiment_train(policy_random_train, 100, 10000, theta)

    # experiment_q_learning(policy_q_table, 1000, 10000, 200)
    # experiment_q_learning2(policy_q_table, 1000)

