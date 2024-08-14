
x = -121

strX = str(x)
for i in range(len(strX)):
    print(i)
    print(strX[i])
    print(strX[-1-i])
    if strX[i]!=strX[-1-i]:
        print("false")
    else:
        print("true")

