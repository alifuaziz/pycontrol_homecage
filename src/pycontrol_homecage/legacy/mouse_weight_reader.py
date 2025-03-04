import numpy as np
import re
import matplotlib.pyplot as plt
import matplotlib
import sys
import numpy as np


def find_prev_base(dat, ctr):
    findbase = True
    rev_ctr = 0
    store = []
    while findbase:
        tmp = re.findall(r"Wbase:([0-9]*\.[0-9]*)_", dat[ctr - rev_ctr])
        if tmp:
            store.append(float(tmp[0]))
            if len(store) > 20:
                findbase = False

        rev_ctr += 1

    wbase = np.mean(store[2:])

    return wbase


def get_mean_dist(dat):
    dists = []
    for i in dat:
        for j in dat:
            if i != j:
                dists.append(np.abs(i - j))
    return np.max(dists)


def find_next_base(dat, ctr):
    findbase = True
    ctr_ = ctr + 0
    store = []
    while findbase:
        tmp = re.findall(r"Wbase:([0-9]*\.[0-9]*)_", dat[ctr_])
        if tmp:
            store.append(float(tmp[0]))
            if len(store) > 20:
                findbase = False
        ctr_ += 1
    wbase = np.mean(store[2:])
    return wbase


def reject_outliers(dat, n_iter=10):
    dat2 = dat.copy()
    for _ in range(n_iter):
        mu = np.median(dat2)
        dat2 = [i for i in dat2 if np.abs(i - mu) < 5]
    return dat2


if __name__ == "__main__":

    # dat = open('C:\\Users\\yweissenberger\\Desktop\\pyhomecage\\setups\\loggers\\test1_-2021-02-05-134602.txt','r').readlines()

    # dat = open('C:\\Users\\yweissenberger\\Desktop\\pyhomecage\\setups\\loggers\\test1_-2021-03-16-124543.txt','r').readlines()
    # dat = open('C:\\Users\\yweissenberger\\Desktop\\pyhomecage\\setups\\loggers\\test1_-2021-02-15-102913.txt','r').readlines()
    dat = open(r"C:\Users\takam\Desktop\pyhomecage\setups\loggers\setup_alpha1_-2021-03-23-174634.txt", "r").readlines()
    ID = "1160000399" + sys.argv[1]
    ws = []
    ts = []
    for ctr, l in enumerate(dat):
        if True:  #'02-12-' in l:
            if ID in l:
                wbase = find_prev_base(dat, ctr)
                # wbase2 = find_next_base(dat,ctr)
                # print(wbase1,wbase2)
                # wbase = np.mean([wbase1,wbase2])
                res = list(
                    reversed(
                        [
                            (float(re.findall(r"temp_w:([0-9]*\.[0-9]*)_", l_)[0]) - wbase)
                            for l_ in dat[ctr - 80 : ctr - 3]
                            if "temp_w" in l_ and "out" not in l_
                        ]
                    )
                )
                # res = reject_outliers(res)
                ws.append(res)
                t_ = float(re.findall(r".*-([0-9]{6})", l)[0])
                ts.append(t_)
                print(t_)

    viridis = matplotlib.cm.get_cmap("inferno", len(ws))
    viridis = viridis(np.linspace(0, 1, len(ws) + 1))
    plt.figure()
    for i, w_ in enumerate(ws):
        plt.plot(w_, color=viridis[i])
    plt.figure()
    plt.plot(ts[:-1], [np.percentile(i, 30) for i in ws][:-1])
    plt.show()
    print("n_visits", len(ws))
    allW = []
    for i in ws:
        filt_w = np.array(
            [0] + [1.0 / (np.abs(i[ix] - j) + np.abs(i[ix + 2] - j)) ** 2 for ix, j in enumerate(i[1:-1])] + [0]
        )
        filt_w /= np.sum(filt_w)
        i = np.array(i)
        hist, bin_edges = np.histogram(i, bins=np.arange(15, 35, 2))
        result = bin_edges[np.argmax(hist)] + 1
        result = np.mean(i[np.logical_and(i > (result - 5), i < (result + 5))])

        RESS = [
            result,
            np.mean(i),
            np.min(i),
            np.max(i),
            np.median(i),
            np.percentile(i, 10),
            np.percentile(i, 30),
            np.percentile(i, 50),
            np.mean(i[1:4]),
            np.sum(filt_w * i),
        ]
        w_ = [np.round(k, decimals=2) for k in RESS]
        print(w_)
        allW.append(w_)

    print(np.array(allW)[:, -1])
    for i in np.array(allW).T:
        print("max", get_mean_dist(i))
