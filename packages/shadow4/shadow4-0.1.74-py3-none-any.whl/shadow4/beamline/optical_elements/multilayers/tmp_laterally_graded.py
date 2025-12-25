# ; memorandum:
# ;
# ;                   ML STACK FOR SHADOW                       THIS EXAMPLE
# ;
# ;                  vacuum
# ;       |------------------------------|  \
# ;       |          odd (n)             |  |
# ;       |------------------------------|  | BILAYER # n        n=60
# ;       |          even (n)            |  |
# ;       |------------------------------|  /
# ;       |          .                   |
# ;       |          .                   |
# ;       |          .                   |
# ;       |------------------------------|  \
# ;       |          odd (1)             |  |                    Pd  (20 A)
# ;       |------------------------------|  | BILAYER # 1
# ;       |          even (1)            |  |                    B4C (20 A)
# ;       |------------------------------|  /
# ;       |                              |
# ;       |///////// substrate //////////|
# ;       |                              |
# ;

import numpy


def write_shadow_surface(s, xx, yy, outFile='presurface.dat'):
    """
      write_shadowSurface: writes a mesh in the SHADOW/presurface format
      SYNTAX:
           out = write_shadowSurface(z,x,y,outFile=outFile)
      INPUTS:
           z - 2D array of heights
           x - 1D array of spatial coordinates along mirror width.
           y - 1D array of spatial coordinates along mirror length.

      OUTPUTS:
           out - 1=Success, 0=Failure
           outFile - output file in SHADOW format. If undefined, the
                     file is names "presurface.dat"

    """
    out = 1

    try:
        fs = open(outFile, 'w')
    except IOError:
        out = 0
        print("Error: can\'t open file: " + outFile)
        return
    else:
        # dimensions
        fs.write(repr(xx.size) + " " + repr(yy.size) + " \n")
        # y array
        for i in range(yy.size):
            fs.write(' ' + repr(yy[i]))
        fs.write("\n")
        # for each x element, the x value and the corresponding z(y)
        # profile
        for i in range(xx.size):
            tmps = ""
            for j in range(yy.size):
                tmps = tmps + "  " + repr(s[j, i])
            fs.write(' ' + repr(xx[i]) + " " + tmps)
            fs.write("\n")
        fs.close()
        print("write_shadow_surface: File for SHADOW " + outFile + " written to disk.")

# if __name__ == "__main__":
if True:
    # ;
    # ; MAIN INPUTS (attention to the units, different from SHADOW standards)
    # ;

    # ;focusing parameters of the elliptical surface
    pp =    33.5 # m
    qq =    1.50 # m
    theta = 0.75 # deg

    mirrorlength = 0.30 #  m
    kev          = 12.4 # keV
    fileRoot     = 'mymultilayer_new'

    # ;  Is the multilayer graded over the surface?
    # ;       0: No
    # ;       1: t and/or gamma graded over the surface (input spline files)
    # ;       2: t graded over the surface (input quadratic fit to t gradient)
    flag_graded = 1

    # ; get refraction indices using dabax
    from dabax.dabax_xraylib import DabaxXraylib
    dx = DabaxXraylib()
    n_even = dx.Refractive_Index_Re('Pd', kev, 12.02)
    n_odd  = dx.Refractive_Index_Re('B4C', kev, 2.52)

    delta_even = 1 - n_even
    delta_odd  = 1 - n_odd


    # ;
    # ; start calculations of ellipse and lateral gradient
    # ;
    import scipy.constants as codata
    lambda1 = codata.h * codata.c / codata.e / (kev * 1e3) * 1e10 # A
    print("lambda1 in A : ", lambda1)

    # ; ellipse axes and eccentricity
    aa = 0.5 * (pp + qq)
    bb = numpy.sqrt(pp * qq) * numpy.sin(theta * numpy.pi / 180)
    cc = numpy.sqrt(aa * aa - bb * bb)
    ee = cc/aa

    # ; ellipse center
    ycen = (pp - qq)/ 2 / ee
    zcen = bb * numpy.sqrt(1 - (ycen / aa)**2)

    # print('wavelength [A]: ',lambda)
    print('ellipse a,b,c: ',aa,bb,cc)
    print('ellipse ycen,zcen: ',ycen,zcen)

    # ; gamma = 0.5
    nn = 0.5 * (n_even + n_odd)

    # ; bilayer dspacing at the surface pole
    bigLambda0 = lambda1 / 2 / numpy.sqrt(nn * nn - (numpy.cos(theta * numpy.pi / 180))**2)
    print('bigLambda0 [A] = ', bigLambda0)

    # ; coordinates along the mirror
    y1  = numpy.linspace(ycen - mirrorlength, ycen + mirrorlength, 100)
    z1  = bb * numpy.sqrt(1 - (y1 * y1 / aa / aa))
    p1 = numpy.sqrt( (cc + y1)**2 + z1**2)
    q1 = numpy.sqrt( (cc - y1)**2 + z1**2)
    beta1 = numpy.arccos( (4 * cc * cc - p1 * p1 - q1 * q1) / (-2) / p1 / q1 )
    alpha1 = (numpy.pi - beta1) / 2
    # ; bilayer dspacing along the surface
    bigLambda = lambda1 / 2 / numpy.sqrt(nn * nn - (numpy.cos(alpha1))**2)

    # ; 2nd-degree polynomial fit of gradient
    cc = numpy.polyfit( (y1 - ycen) * 100, bigLambda / bigLambda0, 2)
    cc = numpy.flip(cc)
    tmps = 'bigL(y) / bigL(y=0) = a0 + a1 * y + a2 * y^2, a=' + repr(cc)
    print(tmps)

    # ;
    # ; plot results
    # ;
    from srxraylib.plot.gol import plot
    plot( (y1 - ycen) * 100, bigLambda / bigLambda0, xtitle='y-ycen [cm]', ytitle='bigLambda / bigLambda0')

    # ;
    # ; write presurface files with gradient
    # ;
    nx = 10
    mirrorwidth = 4.0
    #
    xsurf = numpy.linspace(-mirrorwidth / 2.0, mirrorwidth / 2.0, nx )
    ysurf = (y1 - ycen) * 100
    zsurf = numpy.zeros( (nx, ysurf.size ))

    for i in range(nx):
      zsurf[i, :] = bigLambda / bigLambda0

    write_shadow_surface(zsurf.T, xsurf, ysurf, outFile=fileRoot+'_pre1.dat')
    write_shadow_surface(numpy.ones_like(zsurf.T), xsurf, ysurf, outFile=fileRoot+'_pre2.dat')
    import os
    os.system('cp ' + fileRoot + '_pre1.dat '+ fileRoot + '.dat')
    os.system('cat ' + fileRoot + '_pre2.dat >> ' + fileRoot + '.dat')
    print('File '+fileRoot+'.spl containing ML gradient written to disk.')

    #
    # ; Macro for running pre_mlayer and pre_mlayer_scan
    #
    # ;
    # ; now run SHADOW pre_mlayer
    # ;
    f = open('pre_mlayer.inp', 'w')
    f.write('pre_mlayer\n')
    f.write(fileRoot+'.dat\n')
    f.write('12000.0'  ) # ; from E (eV)
    f.write('\n25000.0'  ) # ; to E (eV)
    f.write('\n2.33'     ) # ; substrate density (Si)
    f.write('\n1'        ) # ; substrate number of species
    f.write('\nSI'       ) # ; \ substrate formula capitalized: Si1
    f.write('\n1'        ) # ; /
    f.write('\n2.52'     ) # ; even layer density (B4C)
    f.write('\n2'        ) # ;\
    f.write('\nBB'       ) # ; \
    f.write('\n4'        ) # ;  \  B4C
    f.write('\nCC'       ) # ;  /
    f.write('\n1'        ) # ; /
    f.write('\n12.0'     ) # ; odd layer density (Pd)
    f.write('\n1'        ) # ;\
    f.write('\nPD'       ) # ; \ Pd
    f.write('\n1'        ) # ; /
    f.write('\n60'       ) # ; number of bilayers
    f.write('\n40.0  0.5  3.1  3.1 ') #  ; bilayer 1: thickness, gamma(even/odd), rough (even), rough(odd)
    f.write('\n-1 -1 -1 -1\n')          #   ; bilayer next: all identical
    f.write("%d\n" % flag_graded)
    if (flag_graded == 1): f.write(fileRoot+'.sha\n') # output file
    if (flag_graded == 1): f.write(fileRoot+'_pre1.dat\n')
    if (flag_graded == 1): f.write(fileRoot+'_pre2.dat\n')
    if (flag_graded == 2): f.write("%f %f %f\n" % (cc[0],cc[1],cc[2]))
    f.write("exit\n")
    f.close()

    print("File pre_mlayer.inp written to disk.")

    #
    # run pre_mlayer in shadow3
    #
    os.system("/home/srio/OASYS1.2/shadow3/shadow3 < pre_mlayer.inp")





