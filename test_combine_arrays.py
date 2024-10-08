import numpy as np

rectangles = [
    [1, 1, 3, 3],
    [3, 1, 4, 2],
    [3, 2, 4, 4],       
]

scores = [0.7, 0.6, 0.5]
classes = ['deer', 'person', 'cat']

combined = np.concatenate([rectangles, np.array(scores).reshape(-1, 1), np.array(classes).reshape(-1, 1)], axis=1)
print(combined)
