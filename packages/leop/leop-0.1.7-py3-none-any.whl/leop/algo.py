def sort(a):
    for i in range(0,len(a)-1):
        for j in range(0,len(a)-i-1):
            if a[j]>a[j+1]:
                a[j],a[j+1]=a[j+1],a[j]
    return a
#打擂台
def max(a):
    max=a[0]
    for i in range(1,len(a)):
        if a[i]>max:
            max=a[i]
    return max
def min(a):
    min=a[0]
    for i in range(1,len(a)):
        if a[i]<min:
            min=a[i]
    return min
def swap(a,b):
    a,b=b,a
    return a,b