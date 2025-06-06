import math
import numpy as np
import random


# helper functions
def getSphereVertexes(
    xRadius=0.75, yRadius=0.75, zRadius=1.5, xc=0, yc=0, zc=0, stacks=6, sectors=6
):
    stackStep = math.pi / stacks
    sectorStep = 2 * math.pi / sectors
    verts = np.empty((3, (stacks + 1) * sectors))
    for i in range(0, stacks + 1):
        stackAngle = math.pi / 2 - i * stackStep
        xr = xRadius * math.cos(stackAngle)
        yr = yRadius * math.cos(stackAngle)
        z = zRadius * math.sin(stackAngle) + zc
        for j in range(0, sectors):
            sectorAngle = j * sectorStep
            # vertex position
            x = xr * math.cos(sectorAngle) + xc
            y = yr * math.sin(sectorAngle) + yc
            verts[0, i * stacks + j] = x
            verts[1, i * stacks + j] = y
            verts[2, i * stacks + j] = z
    return verts


def getSphereTriangles(verts, stacks=6, sectors=6):
    trigVerts = np.empty((((stacks) * sectors * 2), 3, 3))
    ind = 0
    for i in range(0, stacks):
        k1 = i * sectors
        k2 = k1 + sectors
        for j in range(0, sectors):
            k1v = k1 + j
            k1v2 = k1 + ((j + 1) % sectors)
            k2v = k2 + j
            k2v2 = k2 + ((j + 1) % sectors)
            if i != 0:
                trigVerts[ind, 0, :] = verts[:, k1v]
                trigVerts[ind, 1, :] = verts[:, k2v]
                trigVerts[ind, 2, :] = verts[:, k1v2]
                ind += 1
            if i != stacks - 1:
                trigVerts[ind, 0, :] = verts[:, k1v2]
                trigVerts[ind, 1, :] = verts[:, k2v]
                trigVerts[ind, 2, :] = verts[:, k2v2]
                ind += 1
    return trigVerts


def getSphereMesh(
    xRadius=0.75,
    yRadius=0.75,
    zRadius=0.75,
    xc=0,
    yc=0,
    zc=0,
    stacks=6,
    sectors=6,
    bench=0,
):
    verts = getSphereVertexes(
        xRadius=xRadius,
        yRadius=yRadius,
        zRadius=zRadius,
        xc=xc,
        yc=yc,
        zc=zc,
        stacks=stacks,
        sectors=sectors,
    )
    return getSphereTriangles(verts=verts, stacks=stacks, sectors=sectors)


def getBoxVertices(xl, yl, zl, xr, yr, zr):
    verts = np.zeros((8, 3))
    verts[0, :] = [xl, yl, zl]
    verts[1, :] = [xr, yl, zl]
    verts[2, :] = [xl, yr, zl]
    verts[3, :] = [xr, yr, zl]
    verts[4, :] = [xl, yl, zr]
    verts[5, :] = [xr, yl, zr]
    verts[6, :] = [xl, yr, zr]
    verts[7, :] = [xr, yr, zr]
    return verts

def getSquareVertices(xl, yl, zl, xr, yr, zr):
    verts = np.zeros((4, 3))
    verts[0, :] = [xl, yl, zl]
    verts[1, :] = [xr, yl, zl]
    verts[2, :] = [xl, yr, zl]
    verts[3, :] = [xr, yr, zl]
    return verts

def getArcVertices2D(rl,tl,zl,rr,tr,zr):
    verts = np.zeros((20,3))
    theta_granularity = 10
    # inner radius shorter Z
    for i in range(theta_granularity):
        angle = tl + (tr-tl) * i/(theta_granularity-1)
        verts[i,:] = [rl*np.sin(angle * np.pi/180), rl*np.cos(angle * np.pi/180), zl]
    for i in range(theta_granularity):
        angle = tl + (tr-tl) * i/(theta_granularity-1)
        verts[i +  theta_granularity,:] = [rr*np.sin(angle * np.pi/180), rr*np.cos(angle * np.pi/180), zl]
    return verts

def getArcVertices(rl,tl,zl,rr,tr,zr):
    verts = np.zeros((40,3))
    theta_granularity = 10
    # inner radius shorter Z
    for i in range(theta_granularity):
        angle = tl + (tr-tl) * i/(theta_granularity-1)
        verts[i,:] = [rl*np.sin(angle * np.pi/180), rl*np.cos(angle * np.pi/180), zl]
    # inner radius taller Z
    for i in range(theta_granularity):
        angle = tl + (tr-tl) * i/(theta_granularity-1)
        verts[i + theta_granularity,:] = [rl*np.sin(angle * np.pi/180), rl*np.cos(angle * np.pi/180), zr]
    # outer radius shorter Z
    for i in range(theta_granularity):
        angle = tl + (tr-tl) * i/(theta_granularity-1)
        verts[i + 2 * theta_granularity,:] = [rr*np.sin(angle * np.pi/180), rr*np.cos(angle * np.pi/180), zl]
    # inner radius taller Z
    for i in range(theta_granularity):
        angle = tl + (tr-tl) * i/(theta_granularity-1)
        verts[i + 3 * theta_granularity,:] = [rr*np.sin(angle * np.pi/180), rr*np.cos(angle * np.pi/180), zr]
    return verts


def getArcLinesFromVerts2D(verts):
    lines = np.zeros((40,3))
    lines[0] = verts[0]
    lines[1] = verts[10]
    lines[2] = verts[19]
    lines[3] = verts[9]


    for i in range(0, 18, 2):
        lines[4 + i] = verts[int(i/2)]
        lines[5 + i] = verts[int(i/2+1)]

    for i in range(0, 18, 2):
        lines[22 + i] = verts[10 + int(i/2)]
        lines[23 + i] = verts[10 + int(i/2+1)]

    # for i in range(0, 18, 2):
    #     lines[52 + i] = verts[20 + int(i/2)]
    #     lines[53 + i] = verts[20 + int(i/2+1)]    
        
    # for i in range(0, 18, 2):
    #     lines[70 + i] = verts[30 + int(i/2)]
    #     lines[71 + i] = verts[30 + int(i/2+1)]

    return lines

def getArcLinesFromVerts(verts):
    lines = np.zeros((88,3))
    lines[0] = verts[0]
    lines[1] = verts[10]
    lines[2] = verts[10]
    lines[3] = verts[30]
    lines[4] = verts[30]
    lines[5] = verts[20] 
    lines[6] = verts[20] 
    lines[7] = verts[0]
    
    lines[8] = verts[9]
    lines[9] = verts[19]
    lines[10] = verts[19]
    lines[11] = verts[39]
    lines[12] = verts[39]
    lines[13] = verts[29] 
    lines[14] = verts[29] 
    lines[15] = verts[9]

    for i in range(0, 18, 2):
        lines[16 + i] = verts[int(i/2)]
        lines[17 + i] = verts[int(i/2+1)]

    for i in range(0, 18, 2):
        lines[34 + i] = verts[10 + int(i/2)]
        lines[35 + i] = verts[10 + int(i/2+1)]

    for i in range(0, 18, 2):
        lines[52 + i] = verts[20 + int(i/2)]
        lines[53 + i] = verts[20 + int(i/2+1)]    
        
    for i in range(0, 18, 2):
        lines[70 + i] = verts[30 + int(i/2)]
        lines[71 + i] = verts[30 + int(i/2+1)]

    return lines

def getSquareLinesFromVerts(verts):
    lines = np.zeros((8, 3))
    lines[0] = verts[0]
    lines[1] = verts[1]
    lines[2] = verts[1]
    lines[3] = verts[3]
    lines[4] = verts[3]
    lines[5] = verts[2]
    lines[6] = verts[2]
    lines[7] = verts[0]

    return lines

def getBoxLinesFromVerts(verts):
    lines = np.zeros((24, 3))
    # outer loop gets the key vertexes
    # keyVerts = [0,3,5,6]
    # v0
    lines[0] = verts[0]
    lines[1] = verts[1]
    lines[2] = verts[0]
    lines[3] = verts[2]
    lines[4] = verts[0]
    lines[5] = verts[4]
    # v3
    lines[6] = verts[3]
    lines[7] = verts[1]
    lines[8] = verts[3]
    lines[9] = verts[2]
    lines[10] = verts[3]
    lines[11] = verts[7]
    # v5
    lines[12] = verts[5]
    lines[13] = verts[4]
    lines[14] = verts[5]
    lines[15] = verts[7]
    lines[16] = verts[5]
    lines[17] = verts[1]
    # v6
    lines[18] = verts[6]
    lines[19] = verts[2]
    lines[20] = verts[6]
    lines[21] = verts[4]
    lines[22] = verts[6]
    lines[23] = verts[7]
    return lines
    
def getSquareLines(xl,yl,zl,xr,yr,zr):
    verts = getSquareVertices(xl,yl,zl,xr,yr,zr)
    return getSquareLinesFromVerts(verts)

def getBoxLines(xl,yl,zl,xr,yr,zr):
    verts = getBoxVertices(xl,yl,zl,xr,yr,zr)
    return getBoxLinesFromVerts(verts)
    
def getBoxArcs(rl,tl,zl,rr,tr,zr):
    verts = getArcVertices(rl,tl,zl,rr,tr,zr)
    return getArcLinesFromVerts(verts)

def getBoxArcs2D(rl,tl,zl,rr,tr,zr):
    verts = getArcVertices2D(rl,tl,zl,rr,tr,zr)
    return getArcLinesFromVerts2D(verts)


# def getBoxLinesCoords(x,y,z,xrad=0.25,yrad=0.25,zrad=0.5):
#    xl=x-xrad
#    xr=x+xrad
#    yl=y-yrad
#    yr=y+yrad
#    zl=z-zrad
#    zr=z+zrad
#    verts = getBoxVertices(xl,yl,zl,xr,yr,zr)
#    return getBoxLinesFromVerts(verts)

def rotate_vertices(vertices, origin, angle, axis="x"):
    """
    주어진 꼭짓점(vertices)을 특정 origin 기준으로 특정 axis를 중심으로 angle만큼 회전.
    :param vertices: 꼭짓점 배열 (N x 3 형태)
    :param origin: 회전의 중심 (x, y, z)
    :param angle: 회전 각도 (라디안 단위)
    :param axis: 회전 축 ("x", "y", "z")
    :return: 회전된 꼭짓점 배열
    """
    if axis == "x":
        rotation_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(angle), -np.sin(angle)],
            [0, np.sin(angle), np.cos(angle)],
        ])
    elif axis == "y":
        rotation_matrix = np.array([
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],
        ])
    elif axis == "z":
        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1],
        ])
    else:
        raise ValueError("Invalid axis. Choose from 'x', 'y', or 'z'.")

    # 원점을 기준으로 꼭짓점 이동
    translated_vertices = vertices - origin
    # 회전 적용
    rotated_vertices = translated_vertices @ rotation_matrix.T
    # 원점 복구
    return rotated_vertices + origin


def getBoxLinesCoords(x, y, z, track_prediction = 1):
    # for debug
    # if track_prediction == 1:
    #     track_prediction = 3
    body_width = 0.4
    body_height = 0.6
    body_depth = 0.25
    head_size = 0.4
    arm_width = 0.2
    arm_length = 0.6
    leg_width = 0.2
    leg_length = 0.7
    leg_offset = 0.2
    arm_swing_angle = np.radians(30)
    leg_swing_angle = np.radians(30)
    rotation_angle = np.radians(90)
    center = np.array([x, y, z])
    if track_prediction == 1 or track_prediction == 3: # 서 있는 상태 or 앉은 상태
        # 몸
        body_verts = getBoxVertices(x - body_width / 2, y - body_depth / 2, z,
        x + body_width / 2, y + body_depth / 2, z + body_height)
        
        body_lines = getBoxLinesFromVerts(body_verts)

        # 머리
        head_verts = getBoxVertices(x - head_size / 2, y - head_size / 2, z + body_height,
        x + head_size / 2, y + head_size / 2, z + body_height + head_size)

        head_lines = getBoxLinesFromVerts(head_verts)

        # 완팔
        left_arm_verts = getBoxVertices(x - body_width / 2 - arm_width, y - arm_width / 2, z + body_height - arm_length,
        x - body_width / 2, y + arm_width / 2, z + body_height)

        left_shoulder = np.array([x - body_width / 2, y, z + body_height])  # 어깨를 회전 중심으로 설정
        left_arm_verts = rotate_vertices(np.array(left_arm_verts), left_shoulder, -arm_swing_angle, axis="x")
        left_arm_lines = getBoxLinesFromVerts(left_arm_verts)

        # 오른팔
        right_arm_verts = getBoxVertices(x + body_width / 2, y - arm_width / 2, z + body_height - arm_length,
        x + body_width / 2 + arm_width, y + arm_width / 2, z + body_height)

        right_shoulder = np.array([x + body_width / 2, y, z + body_height])  # 어깨 회전
        right_arm_verts = rotate_vertices(np.array(right_arm_verts), right_shoulder, arm_swing_angle, axis="x")
        right_arm_lines = getBoxLinesFromVerts(right_arm_verts)

        if track_prediction == 3: # 서 있는 상태
            # 왼다리
            left_leg_verts = getBoxVertices(x - leg_width / 2 - leg_offset, y - leg_width / 2, z - leg_length,
            x + leg_width / 2 - leg_offset, y + leg_width / 2, z)

            left_pelvis = np.array([x - leg_offset, y, z])  # 회전축(좌표상 다리 최상단 논리상 골반)
            left_leg_verts = rotate_vertices(np.array(left_leg_verts), left_pelvis, leg_swing_angle, axis="x")
            left_leg_lines = getBoxLinesFromVerts(left_leg_verts)

            # 오른다리
            right_leg_verts = getBoxVertices(x - leg_width / 2 + leg_offset, y - leg_width / 2, z - leg_length,
            x + leg_width / 2 + leg_offset, y + leg_width / 2, z)

            right_pelvis = np.array([x + leg_offset, y, z])  # 회전축(좌표상 다리 최상단 논리상 골반)
            right_leg_verts = rotate_vertices(np.array(right_leg_verts), right_pelvis, -leg_swing_angle, axis="x")
            right_leg_lines = getBoxLinesFromVerts(right_leg_verts)
    
        elif track_prediction == 1: # 앉은 상태 프로토타입
            left_leg_verts = getBoxVertices(x - leg_width / 2 - leg_offset, y - leg_width / 2, z - leg_length,
            x + leg_width / 2 - leg_offset, y + leg_width / 2, z)
            
            right_leg_verts = getBoxVertices(x - leg_width / 2 + leg_offset, y - leg_width / 2, z - leg_length,
            x + leg_width / 2 + leg_offset, y + leg_width / 2, z)
            
            left_leg_verts = rotate_vertices(np.array(left_leg_verts), center, rotation_angle, axis="x")
            left_leg_lines = getBoxLinesFromVerts(left_leg_verts)
            
            right_leg_verts = rotate_vertices(np.array(right_leg_verts), center, rotation_angle, axis="x")
            right_leg_lines = getBoxLinesFromVerts(right_leg_verts)
      
    else: # 누운 상태 및 낙상 프로토타입
        # 몸
        body_verts = getBoxVertices(x - body_width / 2, y - body_depth / 2, z,
        x + body_width / 2, y + body_depth / 2, z + body_height)

        body_verts = rotate_vertices(np.array(body_verts), center, rotation_angle, axis="x")
        body_lines = getBoxLinesFromVerts(body_verts)

        # 머리
        head_verts = getBoxVertices(x - head_size / 2, y - head_size / 2, z + body_height,
        x + head_size / 2, y + head_size / 2, z + body_height + head_size)

        head_verts = rotate_vertices(np.array(head_verts), center, rotation_angle, axis="x")
        head_lines = getBoxLinesFromVerts(head_verts)

        # 완팔
        left_arm_verts = getBoxVertices(x - body_width / 2 - arm_width, y - arm_width / 2, z + body_height - arm_length,
        x - body_width / 2, y + arm_width / 2, z + body_height)

        left_arm_verts = rotate_vertices(np.array(left_arm_verts), center, rotation_angle, axis="x")
        left_arm_lines = getBoxLinesFromVerts(left_arm_verts)

        # 오른팔
        right_arm_verts = getBoxVertices(x + body_width / 2, y - arm_width / 2, z + body_height - arm_length,
        x + body_width / 2 + arm_width, y + arm_width / 2, z + body_height)

        right_arm_verts = rotate_vertices(np.array(right_arm_verts), center, rotation_angle, axis="x")
        right_arm_lines = getBoxLinesFromVerts(right_arm_verts)
        
        left_leg_verts = getBoxVertices(x - leg_width / 2 - leg_offset, y - leg_width / 2, z - leg_length,
        x + leg_width / 2 - leg_offset, y + leg_width / 2, z)
        
        right_leg_verts = getBoxVertices(x - leg_width / 2 + leg_offset, y - leg_width / 2, z - leg_length,
        x + leg_width / 2 + leg_offset, y + leg_width / 2, z)
        
        left_leg_verts = rotate_vertices(np.array(left_leg_verts), center, rotation_angle, axis="x")
        left_leg_lines = getBoxLinesFromVerts(left_leg_verts)
        
        right_leg_verts = rotate_vertices(np.array(right_leg_verts), center, rotation_angle, axis="x")
        right_leg_lines = getBoxLinesFromVerts(right_leg_verts)
     
    # 파츠를 죄다 합쳐서 리턴   
    all_lines = np.vstack((body_lines, head_lines, left_arm_lines, right_arm_lines, left_leg_lines, right_leg_lines))

    return all_lines

# Function to rotate a set of coordinates [x,y,z] about the various axis via the tilt angles
# Tilt angles are in degrees
def eulerRot(x, y, z, elevTilt, aziTilt):
    # Convert to radians
    elevTilt = np.deg2rad(elevTilt)
    aziTilt = np.deg2rad(aziTilt)

    elevAziRotMatrix = np.matrix(
        [
            [
                math.cos(aziTilt),
                math.cos(elevTilt) * math.sin(aziTilt),
                math.sin(elevTilt) * math.sin(aziTilt),
            ],
            [
                -math.sin(aziTilt),
                math.cos(elevTilt) * math.cos(aziTilt),
                math.sin(elevTilt) * math.cos(aziTilt),
            ],
            [0, -math.sin(elevTilt), math.cos(elevTilt)],
        ]
    )

    # Old matrix for only Elevation tilt
    # elevRotMatrix = np.matrix([ [ 1,                   0,                  0 ],
    #                             [ 0,  math.cos(elevTilt), math.sin(elevTilt) ],
    #                             [ 0, -math.sin(elevTilt), math.cos(elevTilt) ]
    #                         ])

    target = np.array([[x], [y], [z]])
    rotTarget = elevAziRotMatrix * target
    rotX = rotTarget[0, 0]
    rotY = rotTarget[1, 0]
    rotZ = rotTarget[2, 0]
    return rotX, rotY, rotZ


# Create a list of N distinct colors, visible on the black GUI background, for our tracks
# The format for a single color is (r,g,b,a) -> normalized from 0-255 to 0-1
# LUT based on Kelly's 22 Colors of Max Contrast, slightly adjusted for better visibility on black background (https://sashamaps.net/docs/resources/20-colors/)
# Only the first 21 colors are guaranteed to be highly distinct. After that colors are generated, but not promised to be visually distinct.
def get_trackColors(n):
    # Modified LUT of Kelly's 22 Colors of Max Contrast
    modKellyColors = [
        # (255, 255, 255, 255),   # White
        # (  0,   0,   0, 255),   # Black
        # (169, 169, 169, 255),   # Gray
        (230, 25, 75, 255),  # Red
        (60, 180, 75, 255),  # Green
        (255, 225, 25, 255),  # Yellow
        (67, 99, 216, 255),  # Blue
        (245, 130, 49, 255),  # Orange
        (145, 30, 180, 255),  # Purple
        (66, 212, 244, 255),  # Cyan
        (240, 50, 230, 255),  # Magenta
        (191, 239, 69, 255),  # Lime
        (250, 190, 212, 255),  # Pink
        (70, 153, 144, 255),  # Teal
        (220, 190, 255, 255),  # Lavender
        (154, 99, 36, 255),  # Brown
        (255, 250, 200, 255),  # Beige
        (128, 0, 0, 255),  # Maroon
        (170, 255, 195, 255),  # Mint
        (128, 128, 0, 255),  # Olive
        (255, 216, 177, 255),  # Apricot
        (0, 0, 117, 255),  # Navy
    ]

    # Generate normalized version of Kelly colors
    modKellyColorsNorm = []
    for tup in modKellyColors:
        modKellyColorsNorm.append(tuple(ti / 255 for ti in tup))

    # Create the output color list
    trackColorList = []
    for i in range(n):
        # If within the length of the LUT, just grab values
        if i < len(modKellyColorsNorm):
            trackColorList.append(modKellyColorsNorm[i])
        # Otherwise, generate a color from the average of two randomly selected colors, and add the new color to the list
        else:
            (r_2, g_2, b_2, _) = modKellyColorsNorm[
                random.randint(0, len(modKellyColorsNorm) - 1)
            ]
            (r_1, g_1, b_1, _) = modKellyColorsNorm[
                random.randint(0, len(modKellyColorsNorm) - 1)
            ]
            r_gen = (r_2 + r_1) / 2
            g_gen = (g_2 + g_1) / 2
            b_gen = (b_2 + b_1) / 2
            modKellyColorsNorm.append((r_gen, g_gen, b_gen, 1.0))
            trackColorList.append((r_gen, g_gen, b_gen, 1.0))

    return trackColorList


def getArcVertices(rl, tl, zl, rr, tr, zr):
    verts = np.zeros((40, 3))
    theta_granularity = 10
    # inner radius shorter Z
    for i in range(theta_granularity):
        angle = tl + (tr - tl) * i / (theta_granularity - 1)
        verts[i, :] = [
            rl * np.sin(angle * np.pi / 180),
            rl * np.cos(angle * np.pi / 180),
            zl,
        ]
    # inner radius taller Z
    for i in range(theta_granularity):
        angle = tl + (tr - tl) * i / (theta_granularity - 1)
        verts[i + theta_granularity, :] = [
            rl * np.sin(angle * np.pi / 180),
            rl * np.cos(angle * np.pi / 180),
            zr,
        ]
    # outer radius shorter Z
    for i in range(theta_granularity):
        angle = tl + (tr - tl) * i / (theta_granularity - 1)
        verts[i + 2 * theta_granularity, :] = [
            rr * np.sin(angle * np.pi / 180),
            rr * np.cos(angle * np.pi / 180),
            zl,
        ]
    # inner radius taller Z
    for i in range(theta_granularity):
        angle = tl + (tr - tl) * i / (theta_granularity - 1)
        verts[i + 3 * theta_granularity, :] = [
            rr * np.sin(angle * np.pi / 180),
            rr * np.cos(angle * np.pi / 180),
            zr,
        ]
    return verts


def getArcLinesFromVerts(verts):
    lines = np.zeros((88, 3))
    lines[0] = verts[0]
    lines[1] = verts[10]
    lines[2] = verts[10]
    lines[3] = verts[30]
    lines[4] = verts[30]
    lines[5] = verts[20]
    lines[6] = verts[20]
    lines[7] = verts[0]

    lines[8] = verts[9]
    lines[9] = verts[19]
    lines[10] = verts[19]
    lines[11] = verts[39]
    lines[12] = verts[39]
    lines[13] = verts[29]
    lines[14] = verts[29]
    lines[15] = verts[9]

    for i in range(0, 18, 2):
        lines[16 + i] = verts[int(i / 2)]
        lines[17 + i] = verts[int(i / 2 + 1)]

    for i in range(0, 18, 2):
        lines[34 + i] = verts[10 + int(i / 2)]
        lines[35 + i] = verts[10 + int(i / 2 + 1)]

    for i in range(0, 18, 2):
        lines[52 + i] = verts[20 + int(i / 2)]
        lines[53 + i] = verts[20 + int(i / 2 + 1)]

    for i in range(0, 18, 2):
        lines[70 + i] = verts[30 + int(i / 2)]
        lines[71 + i] = verts[30 + int(i / 2 + 1)]

    return lines


def getBoxArcs(rl, tl, zl, rr, tr, zr):
    verts = getArcVertices(rl, tl, zl, rr, tr, zr)
    return getArcLinesFromVerts(verts)