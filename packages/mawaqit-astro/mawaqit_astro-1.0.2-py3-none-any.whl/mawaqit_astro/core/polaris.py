import math
from ..types import TimeMeasures, NutationResult, PolarisResult
from .utils import sind, cosd, tand, norm360

def compute_polaris(
    time: TimeMeasures,
    nutation: NutationResult,
    sunGeocentricLongitude: float,
    ghaAries: float
) -> PolarisResult:
    TE = time.julianEphemerisCenturies
    TE2 = TE * TE
    TE3 = TE2 * TE

    dtr = math.pi / 180

    # Equatorial coordinates of Polaris at 2000.0 (mean equinox and equator 2000.0)
    RApol0 = 37.95293333
    DECpol0 = 89.26408889

    # Proper motion per year
    dRApol = 2.98155 / 3600
    dDECpol = -0.0152 / 3600

    # Equatorial coordinates at Julian Date T (mean equinox and equator 2000.0)
    RApol1 = RApol0 + 100 * TE * dRApol
    DECpol1 = DECpol0 + 100 * TE * dDECpol

    # Mean obliquity of ecliptic at 2000.0 in degrees
    eps0_2000 = 23.439291111

    # Transformation to ecliptic coordinates in radians (mean equinox and equator 2000.0)
    lambdapol1 = math.atan2(
        (sind(RApol1) * cosd(eps0_2000) + tand(DECpol1) * sind(eps0_2000)),
        cosd(RApol1)
    )

    betapol1 = math.asin(
        sind(DECpol1) * cosd(eps0_2000) - cosd(DECpol1) * sind(eps0_2000) * sind(RApol1)
    )

    # Precession
    eta = (47.0029 * TE - 0.03302 * TE2 + 0.00006 * TE3) * dtr / 3600
    PI0 = (174.876384 - (869.8089 * TE + 0.03536 * TE2) / 3600) * dtr
    p0 = (5029.0966 * TE + 1.11113 * TE2 - 0.0000006 * TE3) * dtr / 3600

    A1 = math.cos(eta) * math.cos(betapol1) * math.sin(PI0 - lambdapol1) - math.sin(eta) * math.sin(betapol1)
    B1 = math.cos(betapol1) * math.cos(PI0 - lambdapol1)
    C1 = math.cos(eta) * math.sin(betapol1) + math.sin(eta) * math.cos(betapol1) * math.sin(PI0 - lambdapol1)

    lambdapol2 = p0 + PI0 - math.atan2(A1, B1)
    betapol2 = math.asin(C1)

    # Nutation in longitude
    lambdapol2 += dtr * nutation.nutationLongitude

    # Aberration
    kappa = dtr * 20.49552 / 3600
    pi0 = dtr * (102.93735 + 1.71953 * TE + 0.00046 * TE2) # Perihelion longitude
    e = 0.016708617 - 0.000042037 * TE - 0.0000001236 * TE2

    dlambdapol = (e * kappa * math.cos(pi0 - lambdapol2) - kappa * math.cos(dtr * sunGeocentricLongitude - lambdapol2)) / math.cos(betapol2)
    dbetapol = -kappa * math.sin(betapol2) * (math.sin(dtr * sunGeocentricLongitude - lambdapol2) - e * math.sin(pi0 - lambdapol2))

    lambdapol2 += dlambdapol
    betapol2 += dbetapol

    # Transformation back to equatorial coordinates in radians
    RApol2 = math.atan2((math.sin(lambdapol2) * cosd(nutation.trueObliquity) - math.tan(betapol2) * sind(nutation.trueObliquity)), math.cos(lambdapol2))
    DECpol2 = math.asin(math.sin(betapol2) * cosd(nutation.trueObliquity) + math.cos(betapol2) * sind(nutation.trueObliquity) * math.sin(lambdapol2))

    # Finals
    GHApol = norm360(ghaAries - RApol2 / dtr)
    SHApol = norm360(360 - RApol2 / dtr)
    DECpol = DECpol2 / dtr

    return PolarisResult(
        rightAscension=RApol2 / dtr,
        declination=DECpol,
        greenwichHourAngle=GHApol,
        siderealHourAngle=SHApol
    )

