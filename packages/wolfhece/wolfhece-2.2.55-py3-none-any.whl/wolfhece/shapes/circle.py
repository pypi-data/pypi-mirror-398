import math
import numpy as np
from numba import jit

""" JIT is a decorator that tells Numba to compile this function using the Numba JIT compiler. """

@jit(nopython=True)
def A_from_h(h:float, diameter:float):
    """ Compute the area of a circular segment from its height """
    d = diameter / 2.0 - h
    theta = math.acos(1.0 - 2.0 * h / diameter)
    chord = math.sqrt(h * (diameter - h))
    area = theta * diameter**2 / 4.0 - chord * d

    return area

@jit(nopython=True)
def dichotomy_A2h(f, a:float, b:float, args, tol=1e-10, max_iter=1000):
    """ Dichotomy algorithm to find the root of a function f between a and b.
    The function f must be defined as f(x, *args) and must return a scalar.
    The function must have a single root in the interval [a, b].
    """
    def cond_fun(val):
        a, b, i = val
        return (b - a) > tol

    def body_fun(val):
        a, b, i = val
        c = (a + b) / 2.
        diameter = args[0]
        fa = f(a, diameter)
        fc = f(c, diameter)
        if fc == 0:
            return (c, c, i + 1)
        else:
            if fa * fc < 0:
                return (a, c, i + 1)
            else:
                return (c, b, i + 1)

    i=0
    while cond_fun((a, b, i)) and i < max_iter:
        a, b, i = body_fun((a, b, 0))

    return (a + b) / 2

@jit(nopython=True)
def segment_of_circle(diameter:float, h:float=None, chord:float=None,
                      arc_length:float=None, area:float=None,
                      from_which:int=None, init_val:bool=None,
                      eps:float=1e-8) -> tuple:
    """ Calcul des caractristiques d'un segment circulaire
    plus d'infos sur http://mathworld.wolfram.com/CircularSegment.html.

    :param diameter: diamtre du cercle [m]
    :param h: hauteur du segment [m]
    :param chord: longueur de la corde [m]
    :param arc_length: longueur de l'arc soutenu par la corde [m]
    :param area: aire du sgment [m]
    :param from_which: variable de calcul sur base de laquelle les autres grandeurs doivent tre values [index dans l'ordre des paramètres (h = 1, area = 4...)]
    :param init_val: utilise h comme valeur initiale pour le calcul de h depuis A [booléen]
    """

    R = diameter / 2.0

    if from_which == 1: # from h
        # The solution is unique

        d = diameter / 2.0 - h
        theta = math.acos(1.0 - 2.0 * h / diameter)

        arc_length = theta * diameter
        chord = math.sqrt(h * (diameter - h))
        area = theta * diameter**2 / 4.0 - chord * d
        chord = 2.0 * chord

    elif from_which == 2: # from chord
        # The solution is not unique --> two possible values for h
        # Conserve the value of h that is the closest to the previous value of h

        # h1 as root of the quadratic equation
        h1 = (diameter - math.sqrt(diameter**2 - chord**2)) / 2.0

        if init_val is not None:
            if init_val:
                h2 = diameter - h1
                dh1 = abs(h - h1)
                dh2 = abs(h + h1 - diameter)

                h = h1 if dh1 < dh2 else h2
            else:
                # Conserve the lowest value of h
                h = h1
        else:
            h = h1

        d = diameter / 2.0 - h
        theta = math.acos(1.0 - 2.0 * h / diameter)

        arc_length = theta * diameter
        area = theta * diameter**2 / 4.0 - chord /2. * d

    elif from_which == 3: # from arc_length
        # The solution is unique

        theta = arc_length / diameter
        h = R * (1.0 - math.cos(theta))
        d = R - h

        chord = math.sqrt(h * (diameter - h))
        area = theta * diameter**2 / 4.0 - chord * d
        chord = 2.0 * chord

    elif from_which in [4,41]: # from area using Newton's method
        # The solution is unique BUT the calculation is iterative

        cur_error = 1.0

        d2by4 = diameter**2 / 4.0
        area_max = math.pi * d2by4

        if area == 0.0:
            h = 0.0
            chord = 0.0
            arc_length = 0.0

        elif area_max > area:
            if init_val is not None:
                if not init_val or h == 0.0:
                    h = R
            else:
                h = R

            while abs(cur_error) > eps:
                d = R - h
                theta = math.acos(1.0 - h / R)
                chord = math.sqrt(h * (diameter - h))
                area_loc = theta * d2by4 - chord * d
                dAdh = chord - ((h - R)**2 - d2by4) / (chord + 1e-200)

                cur_error = (area_loc - area) / dAdh
                if h - cur_error < 0.0:
                    h = h / 2.0
                elif h - cur_error > diameter:
                    h = (h + diameter) / 2.0
                else:
                    h = h - cur_error

            chord = 2.0 * chord
            arc_length = theta * diameter

        else:
            h = diameter
            chord = 0.0
            arc_length = math.pi * diameter

    elif from_which == 42: # from area but using dichotomy rather than Newton-Raphson
        # The solution is unique BUT the calculation is iterative

        cur_error = 1.0

        d2by4 = diameter**2 / 4.0
        area_max = math.pi * d2by4

        if area == 0.0:
            h = 0.0
            chord = 0.0
            arc_length = 0.0

        elif area_max > area:
            if init_val is not None:
                if not init_val or h == 0.0:
                    h = R
            else:
                h = R

            h = dichotomy_A2h(f=A_from_h, a=0., b=diameter, args=(diameter,), tol=eps)

            d = diameter / 2.0 - h
            theta = math.acos(1.0 - 2.0 * h / diameter)
            arc_length = theta * diameter
            chord = math.sqrt(h * (diameter - h))
            chord = 2.0 * chord

        else:
            h = diameter
            chord = 0.0
            arc_length = math.pi * diameter

    return diameter, h, chord, arc_length, area


if __name__ == '__main__':

    diameter = 10.0
    h = 5.0
    chord = -1.
    arc_length = -1.
    area = -1.
    from_which = 1
    init_val = None

    res1 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val)
    diameter, h, chord, arc_length, area = res1

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    from_which = 2
    res2 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val)
    diameter, h, chord, arc_length, area = res2

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    from_which = 2
    res2 = segment_of_circle(diameter, h, chord/2., arc_length, area, from_which, False)
    diameter, h, chord, arc_length, area = res2

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    from_which = 3
    res3 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val)
    diameter, h, chord, arc_length, area = res3

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    from_which = 2
    res2 = segment_of_circle(diameter, h, chord/2., arc_length, area, from_which, init_val)
    diameter, h, chord, arc_length, area = res2

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    diameter = 10.0
    h = 1.
    chord = -1.
    arc_length = -1.
    area = 10.0
    from_which = 4
    init_val = True

    res4 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val)
    diameter, h, chord, arc_length, area = res4

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    diameter = 10.0
    h = -1.
    chord = -1.
    arc_length = -1.
    area = 10.0
    from_which = 4
    init_val = False

    res5 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val)
    diameter, h, chord, arc_length, area = res5

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    diameter = 10.0
    h = 9.
    chord = -1.
    arc_length = -1.
    area = 10.0
    from_which = 4
    init_val = True

    res6 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val)
    diameter, h, chord, arc_length, area = res6

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    diameter = 10.0
    h = 2.
    chord = -1.
    arc_length = -1.
    area = 10.0
    from_which = 4 # from area using Newton's method
    init_val = True

    res7 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val, eps= 1e-12)
    diameter, h, chord, arc_length, area = res7

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")

    diameter = 10.0
    h = 2.
    chord = -1.
    arc_length = -1.
    area = 10.0
    from_which = 42 # from area using dichotomy
    init_val = True

    res8 = segment_of_circle(diameter, h, chord, arc_length, area, from_which, init_val, eps= 1e-12)
    diameter, h, chord, arc_length, area = res7

    print(f"diameter = {diameter}")
    print(f"h = {h}")
    print(f"chord = {chord}")
    print(f"arc_length = {arc_length}")
    print(f"area = {area}")
