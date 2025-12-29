import math

def pos_weights(n, tau=1.5):
    g = [math.exp(-i / tau) for i in range(n)]
    s = sum(g)
    return [x / s for x in g]

def positional_penalty(i, j, order_importance=2.0):
    return math.exp(-abs(i - j) / order_importance)

def _hungarian_min_cost(cost):
    n = len(cost)
    m = len(cost[0])
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, m + 1):
                if used[j]:
                    continue
                cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    ans = [-1] * n
    for j in range(1, m + 1):
        if p[j] != 0:
            ans[p[j] - 1] = j - 1
    return ans

def soft_overlap_bipartite(tokens_a, tokens_b, tokens_order_importance=2.0, tau=1.5, debug=False):
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    n = len(tokens_a)
    m = len(tokens_b)

    wa = pos_weights(n, tau=tau)
    wb = pos_weights(m, tau=tau)

    W = [[0.0] * m for _ in range(n)]
    maxw = 0.0

    for i, a in enumerate(tokens_a):
        for j, b in enumerate(tokens_b):
            s = token_similar(a, b)
            if s == 0.0:
                continue
            p = positional_penalty(i, j, order_importance=tokens_order_importance)
            w = s * p * math.sqrt(wa[i] * wb[j])
            if w > 1.0:
                w = 1.0
            W[i][j] = w
            if w > maxw:
                maxw = w

    k = max(n, m)
    pad = 0.0
    cost = [[maxw - pad for _ in range(k)] for _ in range(k)]
    for i in range(n):
        for j in range(m):
            cost[i][j] = maxw - W[i][j]

    assign = _hungarian_min_cost(cost)

    matched_sum = 0.0
    pairs = []
    for i in range(n):
        j = assign[i]
        if 0 <= j < m:
            w = W[i][j]
            matched_sum += w
            if debug and w > 0.0:
                pairs.append((tokens_a[i], tokens_b[j], w))

    score = (2.0 * matched_sum) / (n + m)
    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0

    if debug:
        print("matched_sum", matched_sum, "n", n, "m", m, "score", score)
        for a, b, w in sorted(pairs, key=lambda x: -x[2]):
            print("PAIR", a, "=>", b, w)

    return score
