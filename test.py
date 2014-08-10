count = 0
L = [1,2,3]
for x in L:
    L.append(x**2)
    print x

    count += 1
    if count > 10:
        break # well shoot