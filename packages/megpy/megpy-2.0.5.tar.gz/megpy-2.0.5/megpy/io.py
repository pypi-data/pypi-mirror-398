_eqdsk_format = {
    0:{'vars':['case','idum','nw','nh'],'size':[4]},
    1:{'vars':['rdim', 'zdim', 'rcentr', 'rleft', 'zmid'],'size':[5]},
    2:{'vars':['rmaxis', 'zmaxis', 'simag', 'sibry', 'bcentr'],'size':[5]},
    3:{'vars':['current', 'simag2', 'xdum', 'rmaxis2', 'xdum'],'size':[5]},
    4:{'vars':['zmaxis2', 'xdum', 'sibry2', 'xdum', 'xdum'],'size':[5]},
    5:{'vars':['fpol'],'size':['nw']},
    6:{'vars':['pres'],'size':['nw']},
    7:{'vars':['ffprim'],'size':['nw']},
    8:{'vars':['pprime'],'size':['nw']},
    9:{'vars':['psirz'],'size':['nh','nw']},
    10:{'vars':['qpsi'],'size':['nw']},
    11:{'vars':['nbbbs','limitr'],'size':[2]},
    12:{'vars':['rbbbs','zbbbs'],'size':['nbbbs']},
    13:{'vars':['rlim','zlim'],'size':['limitr']},
}
_eqdsk_sanity_values = ['rmaxis','zmaxis','simag','sibry'] # specify the sanity values used for consistency check of eqdsk file
_eqdsk_max_values = 5 # maximum number of values per line

def read_geqdsk(f_path):
    """Read an eqdsk g-file from file into `Equilibrium` object

    Args:
        `f_path` (str): the path to the eqdsk g-file, including the file name (!).
        `add_derived` (bool): [True] also add derived quantities (e.g. phi, rho_tor) to the `Equilibrium` object upon reading the g-file, or [False, default] not.

    Returns:
        [default] self
    
    Raises:
        ValueError: Raise an exception when no `f_path` is provided
    """
    if verbose:
        print('Reading eqdsk g-file...')

    # check if eqdsk file path is provided and if it exists
    if f_path is None or not os.path.isfile(f_path):
        raise ValueError('Invalid file or path provided!')
    
    # read the g-file
    with open(f_path,'r') as file:
        lines = file.readlines()
    
    geqdsk = {}
    if lines:
        # start at the top of the file
        current_row = 0
        # go through the eqdsk format key by key and collect all the values for the vars in each format row
        for key in _eqdsk_format:
            if current_row < len(lines):
                # check if the var size is a string refering to a value to be read from the eqdsk file and backfill it, for loop for multidimensional vars
                for i,size in enumerate(_eqdsk_format[key]['size']):
                    if isinstance(size,str):
                        _eqdsk_format[key]['size'][i] = geqdsk[size]

                # compute the row the current eqdsk format key ends
                if len(_eqdsk_format[key]['vars']) != np.prod(_eqdsk_format[key]['size']):
                    end_row = current_row + int(np.ceil(len(_eqdsk_format[key]['vars'])*np.prod(_eqdsk_format[key]['size'])/_eqdsk_max_values))
                else:
                    end_row = current_row + int(np.ceil(np.prod(_eqdsk_format[key]['size'])/_eqdsk_max_values))

                # check if there are values to be collected
                if end_row > current_row:
                    _lines = lines[current_row:end_row]
                    for i_row, row in enumerate(_lines):
                        try:
                            # split the row string into separate values by ' ' as delimiter, adding a space before a minus sign if it is the delimiter
                            values = list(filter(None,re.sub(r'(?<![Ee])-',' -',row).rstrip('\n').split(' ')))
                            # select all the numerical values in the list of sub-strings of the current row, but keep them as strings so the fortran formatting remains
                            numbers = [j for i in [num for num in (re.findall(r'^(?![A-Z]).*-?\ *[0-9]+\.?[0-9]*(?:[Ee]\ *[-+]?\ *[0-9]+)?', value) for value in values)] for j in i]
                            # select all the remaining sub-strings and store them in a separate list
                            strings = [value for value in values if value not in numbers]
                            # handle the exception of the first line where in the case description numbers and strings can be mixed
                            if current_row == 0:
                                numbers = numbers[-3:]
                                strings = [string for string in values if string not in numbers] 
                            # convert the list of numerical sub-strings to their actual int or float value and collate the strings in a single string
                            numbers = [number(value) for value in numbers]
                            strings = ' '.join(strings)
                            _values = numbers
                            if strings:
                                _values.insert(0,strings)
                        except:
                            _values = row.strip()
                        _lines[i_row] = _values
                    # unpack all the values between current_row and end_row in the eqdsk file and flatten the resulting list of lists to a list
                    values = [value for row in _lines for value in row]

                    # handle the exception of len(eqdsk_format[key]['vars']) > 1 and the data being stored in value pairs 
                    if len(_eqdsk_format[key]['vars']) > 1 and len(_eqdsk_format[key]['vars']) != _eqdsk_format[key]['size'][0]:
                        # make a shadow copy of values
                        _values = copy.deepcopy(values)
                        # empty the values list
                        values = []
                        # collect all the values belonging to the n-th variable in the format list and remove them from the shadow value list until empty
                        for j in range(len(_eqdsk_format[key]['vars']),0,-1):
                            values.append(np.array(_values[0::j]))
                            _values = [value for value in _values if value not in values[-1]]
                    # store and reshape the values in a np.array() in case eqdsk_format[key]['size'] > max_values
                    elif _eqdsk_format[key]['size'][0] > _eqdsk_max_values:
                        values = [np.array(values).reshape(_eqdsk_format[key]['size'])]
                    # store the var value pairs in the eqdsk dict
                    geqdsk.update({var:values[k] for k,var in enumerate(_eqdsk_format[key]['vars'])})
                # update the current position in the 
                current_row = end_row
        
        # store any remaining lines as a comment, in case of CHEASE/LIUQE
        if current_row < len(lines):
            comment_lines = []
            for line in lines[current_row+1:]:
                if isinstance(line,list):
                    comment_lines.append(' '.join([str(text) for text in line]))
                else:
                    if line.strip():
                        comment_lines.append(str(line))
            geqdsk['comment'] = '\n'.join(comment_lines)

        # sanity check the eqdsk values
        for key in _eqdsk_sanity_values:
            # find the matching sanity key in eqdsk
            sanity_pair = [keypair for keypair in geqdsk.keys() if keypair.startswith(key)][1]
            #print(sanity_pair)
            if geqdsk[key] != geqdsk[sanity_pair]:
                raise ValueError('Inconsistent '+key+': %7.4g, %7.4g'%(geqdsk[key], geqdsk[sanity_pair])+'. CHECK YOUR EQDSK FILE!')
        
    return geqdsk

def write_geqdsk(f_path):
    """ Write an `Equilibrium` object to an eqdsk g-file 

    Args:
        f_path (str): the target path of generated eqdsk g-file, including the file name (!).
    
    Returns:
        
    """
    if verbose:
        print('Writing Equilibrium to eqdsk g-file...')

    if geqdsk:
        if not isinstance(f_path, str):
            raise TypeError("filepath field must be a string. EQDSK file write aborted.")

        maxv = int(_eqdsk_max_values)

        if os.path.isfile(f_path):
            print("{} exists, overwriting file with EQDSK file!".format(f_path))
        eq = {"xdum": 0.0}
        for linenum in _eqdsk_format:
            if "vars" in _eqdsk_format[linenum]:
                for key in _eqdsk_format[linenum]["vars"]:
                    if key in geqdsk:
                        eq[key] = copy.deepcopy(derived[key])
                    elif key in ["nbbbs","limitr","rbbbs","zbbbs","rlim","zlim"]:
                        eq[key] = None
                        if key in derived:
                            eq[key] = copy.deepcopy(derived[key])
                    else:
                        raise TypeError("%s field must be specified. EQDSK file write aborted." % (key))
        if eq["nbbbs"] is None or eq["rbbbs"] is None or eq["zbbbs"] is None:
            eq["nbbbs"] = 0
            eq["rbbbs"] = []
            eq["zbbbs"] = []
        if eq["limitr"] is None or eq["rlim"] is None or eq["zlim"] is None:
            eq["limitr"] = 0
            eq["rlim"] = []
            eq["zlim"] = []

        eq["xdum"] = 0.0
        with open(f_path, 'w') as ff:
            ff.write("%-48s%4d%4d%4d\n" % (eq["case"], eq["idum"], eq["nw"], eq["nh"]))
            ff.write("%16.9E%16.9E%16.9E%16.9E%16.9E\n" % (eq["rdim"], eq["zdim"], eq["rcentr"], eq["rleft"], eq["zmid"]))
            ff.write("%16.9E%16.9E%16.9E%16.9E%16.9E\n" % (eq["rmaxis"], eq["zmaxis"], eq["simag"], eq["sibry"], eq["bcentr"]))
            ff.write("%16.9E%16.9E%16.9E%16.9E%16.9E\n" % (eq["current"], eq["simag"], eq["xdum"], eq["rmaxis"], eq["xdum"]))
            ff.write("%16.9E%16.9E%16.9E%16.9E%16.9E\n" % (eq["zmaxis"], eq["xdum"], eq["sibry"], eq["xdum"], eq["xdum"]))
            for ii in range(0, len(eq["fpol"])):
                ff.write("%16.9E" % (eq["fpol"][ii]))
                if (ii + 1) % maxv == 0 and (ii + 1) != len(eq["fpol"]):
                    ff.write("\n")
            ff.write("\n")
            for ii in range(0, len(eq["pres"])):
                ff.write("%16.9E" % (eq["pres"][ii]))
                if (ii + 1) % maxv == 0 and (ii + 1) != len(eq["pres"]):
                    ff.write("\n")
            ff.write("\n")
            for ii in range(0, len(eq["ffprim"])):
                ff.write("%16.9E" % (eq["ffprim"][ii]))
                if (ii + 1) % maxv == 0 and (ii + 1) != len(eq["ffprim"]):
                    ff.write("\n")
            ff.write("\n")
            for ii in range(0, len(eq["pprime"])):
                ff.write("%16.9E" % (eq["pprime"][ii]))
                if (ii + 1) % maxv == 0 and (ii + 1) != len(eq["pprime"]):
                    ff.write("\n")
            ff.write("\n")
            kk = 0
            for ii in range(0, eq["nh"]):
                for jj in range(0, eq["nw"]):
                    ff.write("%16.9E" % (eq["psirz"][ii, jj]))
                    if (kk + 1) % maxv == 0 and (kk + 1) != (eq["nh"] * eq["nw"]):
                        ff.write("\n")
                    kk = kk + 1
            ff.write("\n")
            for ii in range(0, len(eq["qpsi"])):
                ff.write("%16.9E" % (eq["qpsi"][ii]))
                if (ii + 1) % maxv == 0 and (ii + 1) != len(eq["qpsi"]):
                    ff.write("\n")
            ff.write("\n")
            ff.write("%5d%5d\n" % (eq["nbbbs"], eq["limitr"]))
            kk = 0
            for ii in range(0, eq["nbbbs"]):
                ff.write("%16.9E" % (eq["rbbbs"][ii]))
                if (kk + 1) % maxv == 0 and (ii + 1) != eq["nbbbs"]:
                    ff.write("\n")
                kk = kk + 1
                ff.write("%16.9E" % (eq["zbbbs"][ii]))
                if (kk + 1) % maxv == 0 and (ii + 1) != eq["nbbbs"]:
                    ff.write("\n")
                kk = kk + 1
            ff.write("\n")
            kk = 0
            for ii in range(0, eq["limitr"]):
                ff.write("%16.9E" % (eq["rlim"][ii]))
                if (kk + 1) % maxv == 0 and (kk + 1) != eq["limitr"]:
                    ff.write("\n")
                kk = kk + 1
                ff.write("%16.9E" % (eq["zlim"][ii]))
                if (kk + 1) % maxv == 0 and (kk + 1) != eq["limitr"]:
                    ff.write("\n")
                kk = kk + 1
            ff.write("\n")
        print('Output EQDSK file saved as {}.'.format(f_path))

    else:
        print("g-eqdsk could not be written")

    return

# GIST routines based on STELLOPT/pySTEL/libstell/gist.py by lazersos
def read_gist(filename):
    """Reads a GIST geometry file

    This routine reads the GIST geometry files.

    Parameters
    ----------
    file : str
        Path to GIST file.
    """
    import numpy as np
    f = open(filename,'r')
    lines = f.readlines()
    f.close()
    i = 0
    temp_dict={}
    while (i < len(lines)):
        if '!s0, alpha0' in lines[i]:
            [txt1,txt2,txteq,s0_txt,alpha0_txt] = lines[i].split()
            s0 = float(s0_txt)
            alpha0 = float(alpha0_txt)
        elif '!major, minor radius[m]=' in lines[i]:
            [txt1,txt2,txt3,Rmajor_txt,Aminor_txt] = lines[i].split()
            Rmajor = float(Rmajor_txt)
            Aminor = float(Aminor_txt)
        elif 'my_dpdx =' in lines[i]:
            [txt1,dpdx_txt] = lines[i].split('=')
            dpdx = float(dpdx_txt)
        elif 'q0 =' in lines[i]:
            [txt1,q0_txt] = lines[i].split('=')
            q0 = float(q0_txt)
        elif 'shat =' in lines[i]:
            [txt1,shat_txt] = lines[i].split('=')
            shat = float(shat_txt)
        elif 'gridpoints =' in lines[i]:
            [txt1,gridpoints_txt] = lines[i].split('=')
            gridpoints = int(gridpoints_txt)
        elif 'n_pol =' in lines[i]:
            [txt1,n_pol_txt] = lines[i].split('=')
            n_pol = int(n_pol_txt)
        elif '/' in lines[i]:
            i0 = i + 1
            g11     = np.zeros(gridpoints)
            g12     = np.zeros(gridpoints)
            g22     = np.zeros(gridpoints)
            Bhat    = np.zeros(gridpoints)
            abs_jac = np.zeros(gridpoints)
            L2      = np.zeros(gridpoints)
            L1      = np.zeros(gridpoints)
            dBdt    = np.zeros(gridpoints)
            for j in range(gridpoints):
                k = i0 + j
                txt        = lines[k].split()
                g11[j]     = float(txt[0])
                g12[j]     = float(txt[1])
                g22[j]     = float(txt[2])
                Bhat[j]   = float(txt[3])
                abs_jac[j] = float(txt[4])
                L2[j]      = float(txt[5])
                L1[j]      = float(txt[6])
                dBdt[j]    = float(txt[7])
            kp1 = L2 - dpdx/2.0/Bhat
        i = i + 1

def write_gist(alpha,maxpnt,vmec_data,s):
    """Compute the GIST quantities from inputs

    This routine computes the various GIST quantities based on a 
    set of user inputs. It mimics the behavior of the STELLOPT
    stellopt_txport code.

    """
    import numpy as np
    from scipy import interpolate
    SEARCH_TOL = 1.0E-12
    s0 = s
    alpha0 = alpha
    Rmajor = vmec_data.rmajor
    Aminor = vmec_data.aminor
    Ba = abs(vmec_data.phi[-1]/(np.pi*vmec_data.aminor*vmec_data.aminor))
    iota = vmec_data.getiota(s)
    iotap = vmec_data.getiotaprime(s)
    pressp = vmec_data.getpressureprime(s)
    mu0 = 4E-7*np.pi
    q = 1.0/iota
    qprime = -iotap*q*q
    shat   = 2*s/q*qprime
    # This comes from GIST
    if (shat < 0.15): shat = 0.0
    dpdx   = np.squeeze(-4.0*np.sqrt(s)/Ba**2 * pressp*mu0)
    theta = np.linspace(-np.pi,np.pi,maxpnt)
    dpdx = dpdx
    q0   = q
    shat = shat
    gridpoints = maxpnt
    n_pol = 1
    g11     = np.zeros(gridpoints)
    g12     = np.zeros(gridpoints)
    g22     = np.zeros(gridpoints)
    Bhat    = np.zeros(gridpoints)
    abs_jac = np.zeros(gridpoints)
    L2      = np.zeros(gridpoints)
    L1      = np.zeros(gridpoints)
    dBdt    = np.zeros(gridpoints)
    for u in range(maxpnt):
        zeta = alpha + q*(theta[u]-0.0)
        zeta = np.mod(zeta,np.pi*2)
        # Compute thetastar (really theta)
        thetastar = vmec_data.getTheta(s,theta[u],zeta)
        thetastar = np.mod(thetastar,np.pi*2)
        # Now compute the Jacobian elements
        R,phi,Z,dRds,dZds,dRdu,dZdu,dRdv,dZdv = vmec_data.get_flxcoord(s,thetastar,zeta)
        # Calc covariant vectors
        esubs = [dRds,0.0,dZds]
        esubu = [dRdu,0.0,dZdu]
        esubv = [dRdv*vmec_data.nfp,R,dZdv*vmec_data.nfp]
        # Calc Jacobian
        sqrtg = R*(dRdu*dZds-dRds*dZdu)
        # Calc contravaiant vectors
        es = np.array([esubu[1]*esubv[2]-esubu[2]*esubv[1],
                        esubu[2]*esubv[0]-esubu[0]*esubv[2],
                        esubu[0]*esubv[1]-esubu[1]*esubv[0]])/sqrtg
        eu = np.array([esubv[1]*esubs[2]-esubv[2]*esubs[1],
                        esubv[2]*esubs[0]-esubv[0]*esubs[2],
                        esubv[0]*esubs[1]-esubv[1]*esubs[0]])/sqrtg
        ev = np.array([esubs[1]*esubu[2]-esubs[2]*esubu[1],
                        esubs[2]*esubu[0]-esubs[0]*esubu[2],
                        esubs[0]*esubu[1]-esubs[1]*esubu[0]])/sqrtg
        # Calc Grad(B)
        th_arr = np.array([[thetastar]])
        ze_arr = np.array([[zeta]])
        print(s,thetastar,zeta)
        b = vmec_data.cfunct(th_arr,ze_arr,vmec_data.bmnc,vmec_data.xm_nyq,vmec_data.xn_nyq)
        bumns = -vmec_data.bmnc*np.tile(vmec_data.xm_nyq,(1,vmec_data.ns)).T
        bvmns =  vmec_data.bmnc*np.tile(vmec_data.xn_nyq,(1,vmec_data.ns)).T
        x = np.linspace(0,1,vmec_data.ns)
        f = np.squeeze(np.diff(b,prepend=0))/np.diff(x,prepend=1)
        modb = np.interp(s,x,np.squeeze(b))
        bs = np.interp(s,x,f)*2.0*np.sqrt(s)
        f = vmec_data.sfunct(th_arr,ze_arr,bumns,vmec_data.xm_nyq,vmec_data.xn_nyq)
        bu = np.interp(s,x,np.squeeze(f))
        f = vmec_data.sfunct(th_arr,ze_arr,bvmns,vmec_data.xm_nyq,vmec_data.xn_nyq)
        bv = np.interp(s,x,np.squeeze(f))
        gradb = bs*es + bu*eu + bv*ev
        # Adjust eu to include lambda factor
        lam = vmec_data.sfunct(th_arr,ze_arr,vmec_data.lmns,vmec_data.xm,vmec_data.xn)
        lumnc =  vmec_data.lmns*np.tile(vmec_data.xm,(1,vmec_data.ns)).T
        lvmnc = -vmec_data.lmns*np.tile(vmec_data.xn,(1,vmec_data.ns)).T
        f = np.squeeze(np.diff(lam,prepend=0))/np.diff(x,prepend=1)
        ls = np.interp(s,x,f)*2.0*np.sqrt(s)
        f = vmec_data.cfunct(th_arr,ze_arr,lumnc,vmec_data.xm,vmec_data.xn)
        lu = np.interp(s,x,np.squeeze(f))
        f = vmec_data.cfunct(th_arr,ze_arr,lvmnc,vmec_data.xm,vmec_data.xn)
        lv = np.interp(s,x,np.squeeze(f))
        eu = eu + ls*es + lu*eu + lv*ev
        # Calc metric elments
        gradA = theta[u]*qprime*es + q*eu - ev
        wrk = np.squeeze(np.array([es[1]*gradA[2]-es[2]*gradA[1],
                        es[2]*gradA[0]-es[0]*gradA[2],
                        es[0]*gradA[1]-es[1]*gradA[0]]))
        jac1 = 1.0/(wrk[0]*eu[0]+wrk[1]*eu[1]+wrk[2]*eu[2])
        gss = np.sum(es*es)
        gsa = np.sum(es*gradA)
        gst = np.sum(es*eu)
        gaa = np.sum(gradA*gradA)
        gat = np.sum(gradA*eu)
        alpha = q*thetastar - zeta
        # Now output the values
        Bhat[u] = modb/Ba
        g11[u]  = gss*Aminor*Aminor*0.25/s
        g12[u]  = gsa*Aminor*Aminor*iota*0.5
        g22[u] = (Bhat[u]*Bhat[u] + g12[u]*g12[u])/g11[u]
        abs_jac[u] = abs(jac1*2*q/Aminor**3)
        # Reuse some variables (order matters)
        ea = np.array([eu[1]*es[2]-eu[2]*es[1],
                        eu[2]*es[0]-eu[0]*es[2],
                        eu[0]*es[1]-eu[1]*es[0]])*jac1
        et = np.array([es[1]*gradA[2]-es[2]*gradA[1],
                        es[2]*gradA[0]-es[0]*gradA[2],
                        es[0]*gradA[1]-es[1]*gradA[0]])*jac1
        es = np.array([gradA[1]*eu[2]-gradA[2]*eu[1],
                        gradA[2]*eu[0]-gradA[0]*eu[2],
                        gradA[0]*eu[1]-gradA[1]*eu[0]])*jac1
        gradB = gradb/Ba
        dBds  = np.sum(gradB*es)
        dBda  = np.sum(gradB*ea)
        dBdt[u] = np.sum(gradB*et)
        c = iota*iota*Aminor**4
        L1[u] = q/np.sqrt(s)*(dBda + c*(gss*gat-gsa*gst)*dBdt[u]/(4*Bhat[u]**2))
        L2[u] = 2.0*np.sqrt(s)*(dBds + c*(gaa*gst-gsa*gat)*dBdt[u]/(4*Bhat[u]**2))
        kp1 = L2 - dpdx/2.0/Bhat
