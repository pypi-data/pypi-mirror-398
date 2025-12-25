"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import math

def f_barr_bathurst(k_sur_D,reynolds):
    r"""
    Evaluation du coefficient de frottement par Barr-Bathurst
    :param k_sur_D : rugosité relative [-]
    :param reynolds : nombre de Reynolds [-] au sens des conduites circulaires --> ATTENTION quand cette fonction est utilisée pour des écoulements à surface libre : Re_prim = 4*Re

    @author Louis Goffin
    @author Pierre Archambeau

    source : TFE O. Machiels - "P:\Documentations\TFE\2008 - O. Machiels"

    La formule habituelle de Barr s'écrit en canalisation (p24 du TFE): \f$ \frac{1}{{\sqrt f }} =  - 2\log \left[ {\frac{{4,518\log \left( {\frac{{{Re} }}{7}} \right)}}{{{Re} \left( {1 + \frac{{{{{Re} }^{0,52}}{{\left( {\frac{k}{D}} \right)}^{0,7}}}}{{29}}} \right)}} + \frac{k}{{3,7D}}} \right] \f$

    Elle est étendue aux macro-rugosités via l'adjonction de la formule de Bathurst (!établie en surface libre!) (p27) : \f$ \sqrt {\frac{1}{f}}  =  - 1,987\log \frac{{{D_{84}}}}{{5,15h}} \f$

    La jonction entre les 2 suit un polynôme : \f$ {\frac{1}{{\sqrt f }} = 1469,76{{\left( {\frac{k}{h}} \right)}^3} - 382,83{{\left( {\frac{k}{h}} \right)}^2} + 9,89\left( {\frac{k}{h}} \right) + 5,22\quad pour\quad 0,05 < \frac{k}{h} < 0,15} \f$

    @remark Les bornes de validité des lois sont exprimées en k_sur_h, c'est-à-dire en 4*k_sur_D

    """
    k_sur_h = 4.0*k_sur_D

    if reynolds<7.0 and k_sur_h <= 0.05:
        #!on suppose une vitesse nulle
        f_barr_bathurst=0.1
        return f_barr_bathurst

    if k_sur_h <= 0.050:
        tmp_f = -2.*math.log10((4.518*math.log10(reynolds/7.))/(reynolds*(1.+reynolds**0.52*k_sur_D**0.7/29.))+k_sur_D/3.7)
    elif k_sur_h > 0.05 and k_sur_h <=0.15:
        tmp_f = 1469.76*k_sur_h**3. - 382.83*k_sur_h**2. + 9.89*k_sur_h + 5.22
    elif k_sur_h > 0.15 and k_sur_h <=0.90:
        tmp_f = -1.987*math.log10(k_sur_h/5.15)
    elif k_sur_h > 0.90 and k_sur_h <=1:
        coeff = (k_sur_h-.9)/.1
        tmp_f = -1.987*math.log10(k_sur_h/5.15) * (1.-coeff) - 1.987*math.log10(1./5.15) * coeff
    else:
        tmp_f = -1.987*math.log10(1./5.15)

    f_barr_bathurst = 1./tmp_f**2.
    return f_barr_bathurst


def f_colebrook(k_sur_D,reynolds):
    r"""
    Evaluation du coefficient de frottement par Colebrook

    :param k_sur_D : rugosité relative [-]
    :param reynolds : nombre de Reynolds [-] au sens des conduites circulaires --> ATTENTION quand cette fonction est utilisée pour des écoulements à surface libre : Re_prim = 4*Re

    @author Pierre Archambeau

    Formule implicite de Colebrook : \f$ \sqrt {\frac{1}{f}}  =  - 2\log \left[ {\frac{k}{{3,7D}} + \frac{{2,51}}{{Re \sqrt f }}} \right] =  - 2\log \left[ {\frac{k}{{14,8{R_h}}} + \frac{{2,51}}{{Re \sqrt f }}} \right] \f$

    Frottement laminaire en section circulaire \f$ \frac{64}{Re} \f$

    Transition par combinaison linéaire entre \f$ 800<Re<1000 \f$

    @remark  Une transition est assurée entre laminaire et turbulent afin de pouvoir utiliser cette fonction dans des procédures itératives
                du type Newton-Raphson qui supportent très mal les fonctions discontinues

    """

    if k_sur_D<0. or reynolds<0.:
        #write(6,*) 'Valeurs de k_sur_D or de reynold inférieure à 0'
        return
    elif k_sur_D>0.05/4.:
        F_Colebrook = f_barr_bathurst(k_sur_D,reynolds)
    else:
        if reynolds<1.e-100:
        # !A VITESSE EST NULLE
            F_Colebrook=0.
        else:
            if reynolds>1000.:
                F_Colebrook=f_colebrook_pure(k_sur_D,reynolds)
            elif reynolds<800:
                # ! LAMINAIRE
                F_Colebrook=64./reynolds
            else:
                pond = (reynolds - 800.)/200.
                F_Colebrook= f_colebrook_pure(k_sur_D,reynolds) *pond + (1.-pond) * 64./reynolds
    return F_Colebrook

def f_colebrook_pure(k_sur_D,reynolds):
    r"""
    Evaluation du coefficient de frottement par Colebrook - pas de test si laminaire
    :param k_sur_D : rugosité relative [-]
    :param reynolds : nombre de Reynolds [-] au sens des conduites circulaires --> ATTENTION quand cette fonction est utilisée pour des écoulements à surface libre : Re_prim = 4*Re

    @author Pierre Archambeau

    Formule implicite de Colebrook : \f$ \sqrt {\frac{1}{f}}  =  - 2\log \left[ {\frac{k}{{3,7D}} + \frac{{2,51}}{{Re \sqrt f }}} \right] =  - 2\log \left[ {\frac{k}{{14,8{R_h}}} + \frac{{2,51}}{{Re \sqrt f }}} \right] \f$
    """

    # !TURBULENT
    prec=1.e-9
    vln10=math.log(10.)

    param1=2.51/vln10/reynolds
    param3=k_sur_D/3.7
    param4=2.51/reynolds

    f1=1.e-2

    vinvracf1=10.
    vinvexpf1=1.e3

    # !VALEUR DE LA PARENTHESE
    dans=param3+param4*vinvracf1
    fdef=vinvracf1+2.*math.log10(dans)
    fprimedef=(-.5-param1/dans)*vinvexpf1

    it=0
    while abs(fdef)>prec:

        f1=f1-fdef/fprimedef

        vinvracf1=1./math.sqrt(f1)
        vinvexpf1=1./(f1**1.5)

        dans=param3+param4*vinvracf1
        fdef=vinvracf1+2.*math.log10(dans)
        fprimedef=(-5e-1-param1/dans)*vinvexpf1
        it+=1

    return f1
