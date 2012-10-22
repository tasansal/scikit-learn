import numpy as np
import pylab as pl
import matplotlib

from scipy.stats.mstats import mquantiles

from sklearn.cross_validation import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import gradient_boosting

X = np.loadtxt('/home/pprett/corpora/cal-housing/cal_housing.data',
               delimiter=',')

names = ['Longitude',
         'Latitude',
         'HouseAge',
         'AveRooms',   # 'totalRooms',
         'AveBedrms',  # 'totalBedrooms',
         'Population',
         'AveOccup',   #  'households',
         'MedInc',
         'medianHouseValue']

y = X[:, -1]
X = X[:, :-1]

# avg rooms
X[:, 3] /= X[:, 6]

# avg bed rooms
X[:, 4] /= X[:, 6]

# avg occupancy
X[:, 6] = X[:, 5] / X[:, 6]

y = y / 100000.0

clf = GradientBoostingRegressor(n_estimators=800, max_depth=4,
                                learn_rate=0.1, loss='huber',
                                random_state=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                    random_state=1)
print("training...")
clf.fit(X_train, y_train)
print("fin.")


def aae(y_true, y_pred):
    return np.mean(np.abs(y_true.ravel() - y_pred.ravel()))


test_score = np.zeros((clf.n_estimators,), dtype=np.float64)
for i, y_pred in enumerate(clf.staged_decision_function(X_test)):
    test_score[i] = aae(y_test, y_pred)

train_score = np.zeros((clf.n_estimators,), dtype=np.float64)
for i, y_pred in enumerate(clf.staged_decision_function(X_train)):
    train_score[i] = aae(y_train, y_pred)

pl.figure()
pl.title('Training and Test Absolute Error')
pl.plot(np.arange(clf.n_estimators) + 1, train_score, 'b-',
        label='Train error')
pl.plot(np.arange(clf.n_estimators) + 1, test_score, 'r-',
        label='Test error')
pl.legend(loc='upper right')
pl.xlabel('Boosting Iterations')
pl.ylabel('Deviance')

pl.figure()

sub_plots = []

for i, fx in enumerate([7, 6, 2, 3]):
    name = names[fx]
    target_feature = np.array([fx], dtype=np.int32)

    ax = pl.subplot(2, 2, i + 1)

    # plot partial dependency
    pdp, (axis,) = gradient_boosting.partial_dependency(clf, target_feature,
                                                        X=X_train)
    ax.plot(axis, pdp.ravel(), 'g-')

    # plot data deciles
    deciles = mquantiles(X_train[:, fx], prob=np.arange(0.1, 1.0, 0.1))
    trans = matplotlib.transforms.blended_transform_factory(ax.transData,
                                                            ax.transAxes)
    ax.vlines(deciles, 0.0, 0.05, transform=trans, color='red')

    pl.xlabel(name)
    pl.ylabel('Partial Dependency')

    sub_plots.append(ax)

# set common ylim
y_min = min((ax.get_ylim()[0] for ax in sub_plots))
y_max = max((ax.get_ylim()[1] for ax in sub_plots))
for ax in sub_plots:
    ax.set_ylim((y_min, y_max))

pl.tight_layout()


from mpl_toolkits.mplot3d import Axes3D
fig = pl.figure()


target_feature = np.array([2, 6], dtype=np.int32)
pdp, (x_axis, y_axis) = gradient_boosting.partial_dependency(clf, target_feature,
                                                             X=X_train,
                                                             grid_resolution=50)
XX, YY = np.meshgrid(x_axis, y_axis)

Z = pdp.T.reshape(XX.shape).T
ax = Axes3D(fig)
surf = ax.plot_surface(XX, YY, Z, rstride=1, cstride=1, cmap=pl.cm.BuPu)

ax.set_xlabel(names[target_feature[0]])
ax.set_ylabel(names[target_feature[1]])
ax.set_zlabel('Partial dependency')

#  pretty init view
ax.view_init(elev=22, azim=122)

pl.colorbar(surf)
