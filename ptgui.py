import json
import numpy as np
from numpy import sqrt, pi, cos, sin, arctan2, float64
import argparse

def deg2rad(d : float64):
    return np.pi * d / 180

def rad2deg(r : float64):
    return 180 * r / np.pi

# https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles

class quaternion:
    w : float64
    x : float64
    y : float64
    z : float64

    def fromEuler(v): # yaw (Z), pitch (Y), roll (X)
        yaw, pitch, roll = v
        #Degree to radius:
        yaw   = deg2rad(yaw)
        pitch = deg2rad(pitch)
        roll  = deg2rad(roll)

        # Abbreviations for the various angular functions
        cy = cos(yaw   * 0.5, dtype=float64)
        sy = sin(yaw   * 0.5, dtype=float64)
        cp = cos(pitch * 0.5, dtype=float64)
        sp = sin(pitch * 0.5, dtype=float64)
        cr = cos(roll  * 0.5, dtype=float64)
        sr = sin(roll  * 0.5, dtype=float64)

        q = quaternion()
        q.w = cy * cp * cr + sy * sp * sr
        q.x = cy * cp * sr - sy * sp * cr
        q.y = sy * cp * sr + cy * sp * cr
        q.z = sy * cp * cr - cy * sp * sr
        return q

    def asEuler(q):
        # roll (x-axis rotation)
        sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
        roll = arctan2(sinr_cosp, cosr_cosp, dtype=float64);

        # pitch (y-axis rotation)
        sinp = sqrt(1 + 2 * (q.w * q.y - q.x * q.z))
        cosp = sqrt(1 - 2 * (q.w * q.y - q.x * q.z))
        pitch = 2 * arctan2(sinp, cosp, dtype=float64) - pi / 2

        # yaw (z-axis rotation)
        siny_cosp =     2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = arctan2(siny_cosp, cosy_cosp, dtype=float64)

        return (rad2deg(yaw), rad2deg(pitch), rad2deg(roll))

    def HamiltonProduct(u, v):
        q = quaternion()
        q.w = u.w*v.w - u.x*v.x - u.y*v.y - u.z*v.z
        q.x = u.w*v.x + u.x*v.w + u.y*v.z - u.z*v.y
        q.y = u.w*v.y - u.x*v.z + u.y*v.w + u.z*v.x
        q.z = u.w*v.z + u.x*v.y - u.y*v.x + u.z*v.w

        return q

###########################

# Access function on ptgui projects

class Ptgui:
    project = None

    def load (filename):
        me = Ptgui()
        with open(filename) as json_file:
            me.project = json.load(json_file)
        return me

    def get_fov(self):
        hfov = self.project['project']['panoramaparams']['hfov']
        vfov = self.project['project']['panoramaparams']['vfov']
        return (hfov, vfov)

    def set_fov(self, fov):
        hfov, vfov = fov
        self.project['project']['panoramaparams']['hfov'] = hfov
        self.project['project']['panoramaparams']['vfov'] = vfov

    def get_position(x):
        y = x['params']['yaw']
        p = x['params']['pitch']
        r = x['params']['roll']
        return (y,p,r)

    def set_position(x, pos):
        y,p,r = pos
        x['params']['yaw'] = y
        x['params']['pitch'] = p
        x['params']['roll'] = r

    def set_resolution(self, res):
        hfov, vfov = self.get_fov()
        hres, vres = res
        r1 = hres/vres
        r2 = hfov/vfov
        if r2 > r1:
            h = hres
            v = h/r2
        else:
            v = vres
            h = v*r2
        pixels = h*v
        self.project['project']['outputsize']['pixels'] = pixels

    def set_projection (self, p):
        self.project['project']["panoramaparams"]["projection"] = p

    def set_seam_blend(self, b):
        self.project['project']['blend']['seamfinding'] = b

    def write_project(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self.project, outfile, indent="  ")

    # rotation using quaternions
    def rotation (self, rot):
        for ig in self.project['project']['imagegroups']:
            pos = Ptgui.get_position (ig['position'])
            q_rot = quaternion.fromEuler(rot)
            pos1 = quaternion.asEuler(quaternion.HamiltonProduct(q_rot, quaternion.fromEuler(pos)))
            Ptgui.set_position(ig['position'], pos1)

            pos = Ptgui.get_position (ig['linkable']['position'])
            pos1 = quaternion.asEuler(quaternion.HamiltonProduct(q_rot, quaternion.fromEuler(pos)))
            Ptgui.set_position(ig['linkable']['position'], pos1)


################################

# Write batch file from project list
def write_batches(fn, projects):
    with open(fn, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<PTGuiBatchList>\n')
        for p in projects:
            f.write('  <Project FileName="' + p + '.pts" Enabled="false" DeleteWhenDone="false"/>\n')
        f.write('</PTGuiBatchList>\n')

def make_range (begin, end, step):
    if end < begin: step = -step
    return range(int(begin), end, step)

from tqdm import tqdm

# Transform data under name according to steps, using function modify to apply each step
def transform(ptgui, res, name, steps, modify):
    projects = []
    for i, h in tqdm(enumerate(steps)):
        modify(ptgui, h)
        project = name + '_' + str(i) + '.pts'
        projects += [project]
        ptgui.set_resolution(res)
        ptgui.write_project(project)
    return projects

# Do the transforms and write the batch file
def do_transforms(ptgui, name, steps, modify):
    projects = transform(ptgui, resolution, name, steps, modify)
    write_batches(name + ".ptgbatch", projects)

resolution = (0,0)

def parse_args():
    global resolution
    res = (0,0)
    parser = argparse.ArgumentParser(
                    prog='ptgui',
                    description='Transform ptgui project files into animations')
    parser.add_argument('filename')
    parser.add_argument('--resolution', nargs=2, type=int)
    parser.add_argument('--transforms', nargs='?')
    args = parser.parse_args()

    if args.resolution != None and len(args.resolution)==2:
        resolution = tuple(args.resolution)

    return args

# Execute transform as described in Dict t
def exec_transform (ptgui, t):
    if t["action"] == "set_vfov": # change vertical field-of-view, maintain aspect ratio
        hfov, vfov = ptgui.get_fov()
        r = make_range (vfov, t["range"][0], t["range"][1])
        do_transforms(ptgui, t["name"], r, lambda p, v : p.set_fov((v*hfov/vfov, v)))
    elif t["action"] == "set_hfov": # change horizontal field-of-view, maintain aspect ratio
        hfov, vfov = ptgui.get_fov()
        r = make_range (hfov, t["range"][0], t["range"][1])
        print (hfov, t["range"][0], t["range"][1])
        do_transforms(ptgui, t["name"], r, lambda p, h : p.set_fov((h, h*vfov/hfov)))
    elif t["action"] == "change_vfov": # change vertical field-of-view, maintain horizontal field-of-view
        hfov, vfov = ptgui.get_fov()
        r = make_range (vfov, t["range"][0], t["range"][1])
        do_transforms(ptgui, t["name"], r, lambda p, h : p.set_fov((hfov, v)))
    elif t["action"] == "change_hfov": # change horizontal field-of-view, maintain vertical field-of-view
        hfov, vfov = ptgui.get_fov()
        r = make_range (hfov, t["range"][0], t["range"][1])
        do_transforms(ptgui, t["name"], r, lambda p, h : p.set_fov((h, vfov)))
    elif t["action"] == "rotate": # rotate according to yaw-pitch-roll
        q = tuple(t["angle"])
        r = make_range (t["range"][0], t["range"][1], t["range"][2])
        do_transforms(ptgui, t["name"], r, lambda p, r : p.rotation(q))
    elif t["action"] == "projection": # change projection type
        ptgui.set_projection(t["value"])
    else:
        print ("Unknown action", t["action"])
        exit(1)

if __name__ == "__main__":
    args = parse_args()
    print(resolution)
    print(args.transforms)

    with open(args.transforms) as json_file:
        transforms = json.load(json_file)

    ptgui = Ptgui.load(args.filename)
    ptgui.set_seam_blend(False) # to prevent flicker

    print ("Transforming ", transforms["name"])
    for t in transforms["transforms"]:
        print ("Action", t["name"])
        exec_transform(ptgui, t)
