#
# Copyright © 2018 United States Government as represented by the Administrator of the 
# National Aeronautics and Space Administration. All Rights Reserved.
#

import time

import numpy as np
import sunpy.map
import sunpy.io
import json
import astropy.units as u
import pandas as pd
from scipy import stats
from scipy.spatial import ConvexHull
from astropy.utils.data import download_file
import urllib
from datetime import datetime, timedelta
import requests
from pyquaternion import Quaternion

# quantity of polygons
n = 21

# domain definition
theta = np.linspace(0, np.pi / 2, n)
phi = np.linspace(0, 2 * np.pi, n)
theta, phi = np.meshgrid(theta, phi)

# Constant for aspect ratio of lemniscate silhouette
AU_REFERENCE_CUBE = 1

# constant for domain and grid inits
GRID_HALF_WIDTH = 800


# function takes care of updating all of the points for the different plots
def plot_update(radial, angular, long, lat):


    # data calculation section for width and distance interaction with figure
    # scalars of the lemniscate
    # c3 is not stored because it is always 1
    lem_distance_c_straight_pixel = (radial * u.solRad).to(u.km) * (
            GRID_HALF_WIDTH / (AU_REFERENCE_CUBE * u.AU).to(u.km))

    c_one = lem_distance_c_straight_pixel
    c_two = c_one * np.tan(((angular / 2) * u.deg))

    x_mod = c_one * np.cos(theta)
    y_mod = c_two * np.cos(theta) * np.sin(theta) * np.cos(phi)
    z_mod = c_two * np.cos(theta) * np.sin(theta) * np.sin(phi)

    # data calculation for latitude and longitude interaction with figure
    v = [x_mod, y_mod, z_mod]

    return rotation(long, lat, v, n)


# function for satellite 3d visuals
# NOTE: Not Used
def functions_sphere(radius, smooth, distance):
    theta = np.linspace(0, 2 * np.pi, smooth)
    phi = np.linspace(0, np.pi, smooth)
    theta, phi = np.meshgrid(theta, phi)

    x = radius * np.cos(theta) * np.sin(phi) + distance
    y = radius * np.sin(theta) * np.sin(phi)
    z = radius * np.cos(phi)

    return np.array([x, y, z])


# quaternion rotation function
def rotation(lo, la, v, smooth):
    q1 = Quaternion(axis=[0.0, 0.0, 1.0], degrees=lo)
    q2 = Quaternion(axis=[0.0, 1.0, 0.0], degrees=la)
    q_rot = q2 * q1

    rot_matrix = q_rot.rotation_matrix
    format_v = np.array(list(zip(np.ravel(v[0]), np.ravel(v[1]), np.ravel(v[2]))))
    format_v = format_v @ rot_matrix

    return np.array(list(map(lambda x: np.reshape(x, (smooth, smooth)), zip(*format_v))))


# function for gamma correction
def gamma_correction(image_data, gamma):
    for i in range(0, len(image_data[1, :])):
        for j in range(0, len(image_data[:, 1])):
            image_data[i, j] = image_data[i, j] ** gamma

    return image_data


# grabs a list of url links upon a date
# 1:STEREO B
# 2:SOHO LASCO C2 zeus
# 3:SOHO LASCO C3 zeus
# 4:STEREO A
def extract_images(date, start_time, end_time, satellite):

    start_time = start_time.split(':')

    date = date.replace(hour=int(start_time[0]), minute=int(start_time[1]))

    frm = (datetime.strftime(date, '%Y-%m-%d %H:%M:%S.%f')).split(' ')

    end_date = date + timedelta(hours=end_time)

    to = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S').split(' ')

    sats = {
        1: 'https://iswa.gsfc.nasa.gov/IswaSystemWebApp/SwpcCATFits?time.min=' + frm[0] + 'T' + frm[1] +
           '&time.max=' + to[0] + 'T' + to[1] + '.0&feed=Stereo-B%20Cor2',
        2: 'https://iswa.gsfc.nasa.gov/IswaSystemWebApp/SwpcCATFits?time.min=' + frm[0] + 'T' + frm[1] +
           '&time.max=' + to[0] + 'T' + to[1] + '.0&feed=SOHO%20C2',
        3: 'https://iswa.gsfc.nasa.gov/IswaSystemWebApp/SwpcCATFits?time.min=' + frm[0] + 'T' + frm[1] +
           '&time.max=' + to[0] + 'T' + to[1] + '.0&feed=SOHO%20C3',
        4: 'https://iswa.gsfc.nasa.gov/IswaSystemWebApp/SwpcCATFits?time.min=' + frm[0] + 'T' + frm[1] +
           '&time.max=' + to[0] + 'T' + to[1] + '.0&feed=Stereo-A%20Cor2',
    }
    instrument = {
        1: 'Stereo-B Cor2',
        2: 'SOHO C2',
        3: 'SOHO C3',
        4: 'Stereo-A Cor2'
    }
    # check if image directory is available, if not return empty array
    try:
        file_link = sats.get(satellite, 'IMPROPER NUMBER, RANGE OF [1,6]')
        files = json.loads(requests.get(file_link).text)
        link_dir = list()

        for file in files[instrument.get(satellite)]['files']:
            link_dir.append(file)

        return np.array(link_dir)

    except urllib.error.URLError:

        return np.empty(1)


# normalizes values to a range of [0,255]
def byte_scale(values):
    return 255 * ((values - values.min()) / (values.max() - values.min()))


# takes in two 2d arrays
# returns the difference of the two arrays
# by comparing each value to it's representation in the other array
def difference_image(current, previous, sat, current_exposure, previous_exposure, sat_id, current_off, previous_off):
    if sat_id == 'LASCO':
        diff = ((np.ravel(current) - current_off) / current_exposure) - (
                (np.ravel(previous) - previous_off) / previous_exposure)
    else:
        diff = byte_scale((np.ravel(current) - current_off) / current_exposure) - byte_scale(
            (np.ravel(previous) - previous_off) / previous_exposure)
    clip = byte_scale(np.clip(diff, -sat, sat))
    return np.reshape(clip, [int(np.sqrt(np.size(clip))), int(np.sqrt(np.size(clip)))])


# NOTE: in order for SOHO LASCO sub map in sunpy to work properly
# NOTE: I had to edit the Dataset formating within the sunpy library
# NOTE: Location of change: sunpy/map/sources/soho.py   line 118
# NOTE: Added: if 'T' not in self.meta['date-obs']:
# takes in two urls and downloads both FITS images
# then rotates, interpolates, corrects, and differance the two
# then returns a new sunpy map, and the rotated and interpolated fits files
def new_map(current_file, previous_file, sat):

    current = header_safe(sunpy.map.Map(current_file))
    previous = header_safe(sunpy.map.Map(previous_file))

    current_offset = current.meta['offset']
    previous_offset = previous.meta['offset']
    current_exposure = current.exposure_time / u.s
    previous_exposure = previous.exposure_time / u.s

    return sunpy.map.Map(difference_image(current.data, previous.data, sat, current_exposure, previous_exposure,
                                          current.instrument, current_offset, previous_offset),
                         current.meta), current, previous


# returns length between the center of the picture and
# the pixel farthest right of it
# also returns the radius of the sun within the pictures perspective
def pic_wcs_length(observer, wx, wy, r_x=256, r_y=256):
    # obtains farthest right pixel in relation to center


    r_x_temp, r_y_temp = observer.reference_pixel

    if 0 <= r_x <= 256:

        r_x *= u.pix

    else:
        r_x = r_x_temp

    if 0 <= r_y <= 256:

        r_y *= u.pix

    else:
        r_y = r_y_temp

    # turn the pixel into WCS
    cc = observer.pixel_to_world(r_x, r_y, 1)
    ca = observer.pixel_to_world(wx * u.pix, wy * u.pix, 1)

    # determines distance between sun and observer
    # obtains it from 'dsun_obs'

    p_r = pic_wcs_solar(observer, all=1)

    # used to get magnitude of the vector point from the cartiesan points
    # cc(arcsec, arcsec) to ca(arcsec, arcsec)

    magnitude_c = np.sqrt((ca.Tx - cc.Tx) ** 2 + (ca.Ty - cc.Ty) ** 2)

    # returns the length of a straight distance
    return (np.tan(magnitude_c) * p_r).to(u.km)


# return either the radius of the observer
# or the longitude, latitude and radius of the observer
# in referance to the sun or
# the Skycords of the observer
def pic_wcs_solar(observer, all=0):
    if all == 0:
        lo = observer.observer_coordinate.lon
        la = observer.observer_coordinate.lat
        r = observer.observer_coordinate.radius
        return lo, la, r
    if all == 1:
        return observer.observer_coordinate.radius
    else:
        return observer.observer_coordinate


# edits LASCO FITS files so they don't produce a lot of warning messages
# also speeds up calculation by having the satellite not
# continue to access the .get_earth function
def header_safe(current):
    if current.instrument == 'LASCO':
        if 'hgln_obs' not in current.meta:
            temp_earth = sunpy.coordinates.get_earth(time=current.date)
            current.meta['hgln_obs'] = '0'
            current.meta['hglt_obs'] = temp_earth.lat
            current.meta['dsun_obs'] = temp_earth.radius
    return current.rotate(order=3, recenter=True).resample((256, 256) * u.pix, 'linear')


# calculates json data for lemniscate plotting

def calc_plot_json(observer, sat_id, radial, angular, long, lat):

    if sat_id == 0:

        v = plot_update(radial, angular, -long, lat)

        v = rotation(observer.observer_coordinate.lon / u.deg + 90, -observer.observer_coordinate.lat / u.deg, v, n)

    else:
        v = plot_update(radial, angular, -long, lat)

        v = rotation(observer.observer_coordinate.lon / u.deg + 90, observer.observer_coordinate.lat / u.deg, v, n)

    points = np.array(list(zip(np.ravel(v[0]), np.ravel(v[2]))))
    hull = ConvexHull(points, qhull_options='QbB')

    # sun center point on the picture
    # obtains CRVAL1 = r_x and CRVAL = r_y
    sun_x_center, sun_y_center = observer.reference_pixel

    # used to determine how far the lemniscate must be moved
    # due to the picture not having the sun in the exact center
    # 128 = have of the dimensions of the plot

    x_translate = (sun_x_center / u.pix) - 128
    y_translate = (sun_y_center / u.pix) - 128

    # determines aspect ratio for distance from satellite
    pic_width_ratio = pic_wcs_length(observer, 256, 128, r_x=128, r_y=128)

    lem_distance_c_ratio = (AU_REFERENCE_CUBE * u.AU).to(u.km) / pic_width_ratio

    hull = np.array(((points[hull.vertices, 0] * lem_distance_c_ratio + x_translate),
                     (points[hull.vertices, 1] * lem_distance_c_ratio + y_translate)))

    return json.dumps(hull.tolist())


# calculates json data for image plotting

def calc_image_json(image_data, gamma, stretch_top, stretch_bot):

    # stretch bottom and top
    image_data = np.clip(image_data, stretch_top, stretch_bot)

    # correct image based on slider value
    image_data = gamma_correction(image_data, gamma)

    return json.dumps(image_data.tolist())


# returns plot data
def return_plot(observer, sat_id, radial, angular, long, lat):
    return np.array(pd.read_json(calc_plot_json(observer, sat_id, radial, angular, long, lat,)))


# returns image data
def return_image(image_data, gamma, stretch_top, stretch_bot):
    return np.array(json.loads(calc_image_json(image_data, gamma, stretch_top, stretch_bot)))
