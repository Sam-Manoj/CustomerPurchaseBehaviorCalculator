from django.shortcuts import render
import numpy as np
import json

def calculation_page(request):
    
    states = ['Browsing', 'Considering', 'Buying']
    observations = ['Click', 'AddToCart', 'Payment', 'Review']
    pi_default = np.array([0.6, 0.3, 0.1])
    trans_default = np.array([
        [0.7, 0.2, 0.1],
        [0.3, 0.5, 0.2],
        [0.2, 0.3, 0.5]
    ])
    emission_default = np.array([
        [0.7, 0.2, 0.0, 0.1],
        [0.2, 0.5, 0.1, 0.2],
        [0.1, 0.2, 0.5, 0.2]
    ])
    obs_sequence_names = ['Click', 'AddToCart', 'Payment', 'Review']
    obs_map = {name: i for i, name in enumerate(observations)}
    obs_sequence = np.array([obs_map[o] for o in obs_sequence_names])

    N = len(states)
    T = len(obs_sequence)
    error_message = None

    if request.method == "POST":
        try:
            pi = np.array([float(request.POST.get(f'pi_{i}')) for i in range(N)])
            trans = np.zeros((N, N))
            for i in range(N):
                trans[i, :] = [float(request.POST.get(f'trans_{i}_{j}')) for j in range(N)]
            emission = np.zeros((N, len(observations)))
            for i in range(N):
                emission[i, :] = [float(request.POST.get(f'emission_{i}_{j}')) for j in range(len(observations))]
            if not np.isclose(np.sum(pi), 1.0):
                error_message = "Initial probabilities (π) do not sum to 1.0."
        except (ValueError, TypeError):
            error_message = "Invalid input. Please ensure all probabilities are numbers."
            # Reset to default if input is bad
            pi = pi_default
            trans = trans_default
            emission = emission_default
    else:
        # Load defaults on GET request
        pi = pi_default
        trans = trans_default
        emission = emission_default

    viterbi = np.zeros((N, T))
    backpointer = np.zeros((N, T), dtype=int)
    viterbi[:, 0] = pi * emission[:, obs_sequence[0]]

    # Recursion Step
    for t in range(1, T):
        for s in range(N):
            prob = viterbi[:, t-1] * trans[:, s] * emission[s, obs_sequence[t]]
            viterbi[s, t] = np.max(prob)
            backpointer[s, t] = np.argmax(prob)

    # Termination Step
    best_last_state = np.argmax(viterbi[:, T-1])
    best_path_prob = np.max(viterbi[:, T-1])
    
    best_path = [best_last_state]
    for t in range(T-1, 0, -1):
        best_last_state = backpointer[best_last_state, t]
        best_path.insert(0, best_last_state)

    most_likely_states = [states[i] for i in best_path]
    viterbi_data_json = json.dumps(viterbi.tolist()) # For the graph

    forward = np.zeros((N, T))

    forward[:, 0] = pi * emission[:, obs_sequence[0]]

    for t in range(1, T):
        for s in range(N): # For each current state 's'
            # Sum of probabilities from all previous states 'j'
            sum_prob = np.sum(forward[:, t-1] * trans[:, s])
            forward[s, t] = sum_prob * emission[s, obs_sequence[t]]

    # Termination Step
    total_likelihood = np.sum(forward[:, T-1])

    context = {
        'states': states,
        'observations': observations,
        'initial_prob': pi,
        'transitions': trans,
        'emissions': emission,
        'obs_sequence_names': obs_sequence_names,
        'obs_sequence_names_json': json.dumps(obs_sequence_names),
        
        # Viterbi Results
        'most_likely_states': most_likely_states,
        'viterbi_prob': best_path_prob,
        'viterbi_data_json': viterbi_data_json,
        
        # Forward Algorithm Result
        'forward_prob': total_likelihood,
        'error_message': error_message,
    }

    return render(request, 'cal/calculation.html', context)

