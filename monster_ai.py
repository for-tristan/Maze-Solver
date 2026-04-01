
import heapq

# movements 
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

# distance
def distance(a, b):
    
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# identifiers for monster player and maze 
def identify(start, goal, maze):
    rows = len(maze)
    cols = len(maze[0]) # size 

    prediction = [] #title prediction
    heapq.heappush(prediction, (0, start))

    spawn = {} #spawn point 
    oldp = {start: 0} 

    while prediction:
        _, current = heapq.heappop(prediction)

        if current == goal: #reverse spawn path
            path = [current]
            while current in spawn:
                current = spawn[current]
                path.append(current)
            path.reverse()
            return path

        for dx, dy in DIRS: #check surronds
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] == 0: #ignore walls go empty title
                score = oldp[current] + 1
                if (nx, ny) not in oldp or score < oldp[(nx, ny)]:  #if surrounded tiles are not a past tile go in them and find better path
                    spawn[(nx, ny)] = current
                    oldp[(nx, ny)] = score
                    f = score + distance((nx, ny), goal) #tile calc for best path for shorter distance 
                    heapq.heappush(prediction, (f, (nx, ny)))

    return None


def move(monstersight, playersight, maze): #calling A star algo
    start = tuple(monstersight)
    goal = tuple(playersight)

    path = identify(start, goal, maze) # figuring out the maze

    if path and len(path) > 1:  #move only 1 title at a time 
        nx, ny = path[1]  #configure speed in game.py ya george
        return nx - monstersight[0], ny - monstersight[1]

    return (0, 0) #monster stops movinh when player finds end
