class STATE:
    STATE_FALL = 0
    STATE_SIT = 1
    STATE_LIE_DOWN = 2
    STATE_WALK = 3

    TICKET_GREEN = 30
    TICKET_RED = 150

class CLUSTER_CACHE:
    DISTANCE_THRESHOLD = 0    # cluster x, y 좌표간 squared 거리 기반 같은 클러스터 판별 임계값
    XPOS = 0
    YPOS = 1
    TICKET = 2
    STATE = 3
    PID = 4

    TICKET_UPDATE = 10

NUM_OF_DETECT_PEOPLE = 3

xPos = 0.12
yPos = 0.1


used_people_id = set([9,3,4,10,2])
clust_cache = [[0.1, 0.1, 3, 0, 3], [0.5, 0.7, 5, 0, 4], [-0.2, 0.1, 7, 0, 9], [-0.2, 0.1, 1, 0, 10], [-0.2, 0.1, 2, 0, 1] ]


near_clust_flag = False

del_elem = []
for idx, elem in enumerate(clust_cache):
    # ticket calc
    elem[CLUSTER_CACHE.TICKET] -= 1
    if elem[CLUSTER_CACHE.TICKET] < 1:
        # expired
        del_elem.append(elem)
        used_people_id.remove(elem[CLUSTER_CACHE.PID])
        continue

    sq_dist = (elem[CLUSTER_CACHE.XPOS] - xPos)**2 + (elem[CLUSTER_CACHE.YPOS] - yPos)**2
    
    if sq_dist < CLUSTER_CACHE.DISTANCE_THRESHOLD:
        # print(sq_dist, " : " ,elem[CLUSTER_CACHE.XPOS], elem[CLUSTER_CACHE.YPOS])
        if near_clust_flag == False:
            near_clust_flag = True
            near_clust = (sq_dist, elem[CLUSTER_CACHE.XPOS], elem[CLUSTER_CACHE.YPOS], idx)
        else:
            if near_clust[0] > sq_dist:
                near_clust = (sq_dist, elem[CLUSTER_CACHE.XPOS], elem[CLUSTER_CACHE.YPOS], idx)

# delete expired entry
for elem in del_elem:
    clust_cache.remove(elem)

if near_clust_flag:
    # update cache
    clust_cache[near_clust[3]] = [xPos, yPos, CLUSTER_CACHE.TICKET_UPDATE, clust_cache[near_clust[3]][3], clust_cache[near_clust[3]][4]]
else:
    new_id = 1
    while new_id in used_people_id:
        new_id += 1

    if new_id > NUM_OF_DETECT_PEOPLE:   # pid overflowed
        # find max ticket
        min = CLUSTER_CACHE.TICKET_UPDATE
        min_idx = 1
        for idx, elem in enumerate(clust_cache):
            if min > elem[CLUSTER_CACHE.TICKET]:
                min_idx = idx + 1
                min = elem[CLUSTER_CACHE.TICKET]
        clust_cache[min_idx] = [xPos, yPos, CLUSTER_CACHE.TICKET_UPDATE, STATE.STATE_WALK, clust_cache[min_idx][4]]

    used_people_id.add(new_id)
    clust_cache.append([xPos, yPos, CLUSTER_CACHE.TICKET_UPDATE, STATE.STATE_WALK, new_id])

print(clust_cache)
print(used_people_id)


# print(near_clust)