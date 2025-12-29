    
    
def intersection(A, B):
    if A is None or B is None:
        return None
    
    return set(A).intersection(B)


def intersection_positions(A, B):
    setB = set(B)
    seen = set()
    return [idx for idx, elem in enumerate(A) 
            if elem in setB and elem not in seen and not seen.add(elem)]
    
if __name__ == "__main__":
    
    a = [1,2, 3, 4,5, 6, 7, 8, 9]
    b = [1,5,8]
    da = [[1,2,3], [21, 22, 23], [31,32,33],[41,42,43],[51,52,53],[61,62,63],[71,72,73],[81,82,83], [91,92,93]]
    
    c = intersection(a, b)    
    print(c)
    
    d = intersection_positions(a, b)
    print(d)
    
    d1 = [da[i] for i in d]
    print(d1)