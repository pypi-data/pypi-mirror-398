from radboy.DB.db import *
from radboy.DB.RandomStringUtil import *
import radboy.Unified.Unified as unified
import radboy.possibleCode as pc
from radboy.DB.Prompt import *
from radboy.DB.Prompt import prefix_text
from radboy.TasksMode.ReFormula import *
from radboy.TasksMode.SetEntryNEU import *
from radboy.FB.FormBuilder import *
from radboy.FB.FBMTXT import *
from radboy.RNE.RNE import *
from radboy.Lookup2.Lookup2 import Lookup as Lookup2
from radboy.DayLog.DayLogger import *
from radboy.DB.masterLookup import *
from collections import namedtuple,OrderedDict
import nanoid,qrcode,io
from password_generator import PasswordGenerator
import random
from pint import UnitRegistry
import pandas as pd
import numpy as np
from datetime import *
from colored import Style,Fore
import json,sys,math,re,calendar,hashlib,haversine
from time import sleep
import itertools
import decimal
from decimal import localcontext,Decimal
unit_registry=pint.UnitRegistry()
import math,scipy
from radboy.HowDoYouDefineMe.CoreEmotions import *
from radboy.DB.glossary_db import *

def volume():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        #print(f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow}")
        height=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} height?: ",helpText="height=1",data="dec.dec")
        if height is None:
            return
        elif height in ['d',]:
            height=Decimal('1')
        
        width=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} width?: ",helpText="width=1 ",data="dec.dec")
        if width is None:
            return
        elif width in ['d',]:
            width=Decimal('1')
    


        length=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length?: ",helpText="length=1",data="dec.dec")
        if length is None:
            return
        elif length in ['d',]:
            length=Decimal('1')

        return length*width*height

def volume_pint():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        height=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} height?: ",helpText="height=1",data="string")
        if height is None:
            return
        elif height in ['d',]:
            height='1'
        
        width=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} width?: ",helpText="width=1 ",data="string")
        if width is None:
            return
        elif width in ['d',]:
            width='1'
        


        length=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length?: ",helpText="length=1",data="string")
        if length is None:
            return
        elif length in ['d',]:
            length='1'

        return unit_registry.Quantity(length)*unit_registry.Quantity(width)*unit_registry.Quantity(height)

def inductance_pint():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        relative_permeability=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} relative_permeability?: ",helpText="relative_permeability(air)=1",data="string")
        if relative_permeability is None:
            return
        elif relative_permeability in ['d',]:
            relative_permeability='1'
        relative_permeability=float(relative_permeability)

        turns_of_wire_on_coil=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} turns_of_wire_on_coil?: ",helpText="turns_of_wire_on_coil=1",data="string")
        if turns_of_wire_on_coil is None:
            return
        elif turns_of_wire_on_coil in ['d',]:
            turns_of_wire_on_coil='1'
        turns_of_wire_on_coil=int(turns_of_wire_on_coil)

        #convert to meters
        core_cross_sectional_area_meters=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} core_cross_sectional_area_meters?: ",helpText="core_cross_sectional_area_meters=1",data="string")
        if core_cross_sectional_area_meters is None:
            return
        elif core_cross_sectional_area_meters in ['d',]:
            core_cross_sectional_area_meters='1m'
        try:
            core_cross_sectional_area_meters=unit_registry.Quantity(core_cross_sectional_area_meters).to("meters")
        except Exception as e:
            print(e,"defaulting to meters")
            core_cross_sectional_area_meters=unit_registry.Quantity(f"{core_cross_sectional_area_meters} meters")

        length_of_coil_meters=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length_of_coil_meters?: ",helpText="length_of_coil_meters=1",data="string")
        if length_of_coil_meters is None:
            return
        elif length_of_coil_meters in ['d',]:
            length_of_coil_meters='1m'
        try:
            length_of_coil_meters=unit_registry.Quantity(length_of_coil_meters).to('meters')
        except Exception as e:
            print(e,"defaulting to meters")
            length_of_coil_meters=unit_registry.Quantity(f"{length_of_coil_meters} meters")
        
        numerator=((turns_of_wire_on_coil**2)*core_cross_sectional_area_meters)
        f=relative_permeability*(numerator/length_of_coil_meters)*1.26e-6
        f=unit_registry.Quantity(f"{f.magnitude} H")
        return f

def resonant_inductance():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        hertz=1e9
        while True:
            try:
                hertz=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} frequency in hertz[530 kilohertz]? ",helpText="frequency in hertz",data="string")
                if hertz is None:
                    return
                elif hertz in ['d','']:
                    hertz="530 megahertz"
                print(hertz)
                x=unit_registry.Quantity(hertz)
                if x:
                    hertz=x.to("hertz")
                else:
                    hertz=1e6
                break
            except Exception as e:
                print(e)

        
        while True:
            try:
                capacitance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} capacitance[365 picofarads]? ",helpText="capacitance in farads",data="string")
                if capacitance is None:
                    return
                elif capacitance in ['d',]:
                    capacitance="365 picofarads"
                x=unit_registry.Quantity(capacitance)
                if x:
                    x=x.to("farads")
                farads=x.magnitude
                break
            except Exception as e:
                print(e)

        inductance=1/(decc(4*math.pi**2)*decc(hertz.magnitude**2,cf=13)*decc(farads,cf=13))

        L=unit_registry.Quantity(inductance,"henry")
        return L

def air_coil_cap():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''C = 1 / (4π²f²L)'''
        while True:
            try:
                frequency=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} frequency? ",helpText="frequency",data="string")
                if frequency is None:
                    return
                elif frequency in ['d',]:
                    frequency="1410 kilohertz"
                x=unit_registry.Quantity(frequency)
                if x:
                    x=x.to("hertz")
                frequency=decc(x.magnitude**2)
                break
            except Exception as e:
                print(e)
        
        while True:
            try:
                inductance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} inductance(356 microhenry): ",helpText="coil inductance",data="string")
                if inductance is None:
                    return
                elif inductance in ['d',]:
                    inductance="356 microhenry"
                x=unit_registry.Quantity(inductance)
                if x:
                    x=x.to("henry")
                inductance=decc(x.magnitude,cf=20)
                break
            except Exception as e:
                print(e)
        

        
        farads=1/(inductance*frequency*decc(4*math.pi**2))
        return unit_registry.Quantity(farads,"farad")

def air_coil():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        The formula for inductance - using toilet rolls, PVC pipe etc. can be well approximated by:


                          0.394 * r2 * N2
        Inductance L = ________________
                         ( 9 *r ) + ( 10 * Len)
        Here:
        N = number of turns
        r = radius of the coil i.e. form diameter (in cm.) divided by 2
        Len = length of the coil - again in cm.
        L = inductance in uH.
        * = multiply by
        '''
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} diameter in cm [2 cm]? ",helpText="diamater of coil",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="2 cm"
                x=unit_registry.Quantity(diameter)
                if x:
                    x=x.to("centimeter")
                diameter=x.magnitude
                break
            except Exception as e:
                print(e)
        radius=decc(diameter/2)
        while True:
            try:
                length=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length in cm [2 cm]? ",helpText="length of coil",data="string")
                if length is None:
                    return
                elif length in ['d',]:
                    length="2 cm"
                x=unit_registry.Quantity(length)
                if x:
                    x=x.to("centimeter")
                length=x.magnitude
                break
            except Exception as e:
                print(e)
        while True:
            try:
                turns=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} number of turns? ",helpText="turns of wire",data="integer")
                if turns is None:
                    return
                elif turns in ['d',]:
                    turns=1
                LTop=decc(0.394)*decc(radius**2)*decc(turns**2)
                LBottom=(decc(9)*radius)+decc(length*10)
                L=LTop/LBottom
                print(pint.Quantity(L,'microhenry'))
                different_turns=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} use a different number of turns?",helpText="yes or no",data="boolean")
                if different_turns is None:
                    return
                elif different_turns in ['d',True]:
                    continue
                break
            except Exception as e:
                print(e)

        
        return pint.Quantity(L,'microhenry')

def circumference_diameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} diameter unit[4 cm]? ",helpText="diamater with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="4 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude/2),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(2*math.pi)*decc(radius.magnitude)

            return pint.Quantity(result,radius.units)
        else:
            return

def circumference_radius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} radius unit[2 cm]? ",helpText="radius with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="2 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(2*math.pi)*decc(radius.magnitude)

            return pint.Quantity(result,radius.units)
        else:
            return

def area_of_circle_radius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
    A = πr²
        '''
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} radius unit[2 cm]? ",helpText="radius with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="2 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(math.pi)*decc(radius.magnitude**2)

            return pint.Quantity(result,radius.units)
        else:
            return

def lc_frequency():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        inductance=None
        capacitance=None
        while True:
            try:
                inductance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} inductance(356 microhenry): ",helpText="coil inductance",data="string")
                if inductance is None:
                    return
                elif inductance in ['d',]:
                    inductance="356 microhenry"
                x=unit_registry.Quantity(inductance)
                if x:
                    x=x.to("henry")
                inductance=decc(x.magnitude,cf=20)
                break
            except Exception as e:
                print(e)
        while True:
            try:
                capacitance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} capacitance[365 picofarads]? ",helpText="capacitance in farads",data="string")
                if capacitance is None:
                    return
                elif capacitance in ['d',]:
                    capacitance="365 picofarads"
                x=unit_registry.Quantity(capacitance)
                if x:
                    x=x.to("farads")
                farads=decc(x.magnitude,cf=20)
                break
            except Exception as e:
                print(e)
        frequency=1/(decc(2*math.pi)*decc(math.sqrt(farads*inductance),cf=20))
        return unit_registry.Quantity(frequency,"hertz")

def area_of_circle_diameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
    A = πr²
        '''
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} diameter unit[4 cm]? ",helpText="diamater value with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="4 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude/2),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(math.pi)*decc(radius.magnitude**2)

            return pint.Quantity(result,radius.units)
        else:
            return


def area_triangle():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        height=None
        base=None
        '''
        A=hbb/2
        '''
        while True:
            try:
                base=Control(func=FormBuilderMkText,ptext="base",helpText="base width",data="string")
                if base is None:
                    return
                elif base in ['d',]:
                    base=unit_registry.Quantity('1')
                else:
                    base=unit_registry.Quantity(base)
                break
            except Exception as e:
                print(e)
                try:
                    base=Control(func=FormBuilderMkText,ptext="base no units",helpText="base width,do not include units",data="dec.dec")
                    if base is None:
                        return
                    elif base in ['d',]:
                        base=decc(1)
                    break
                except Exception as e:
                    continue

        while True:
            try:
                height=Control(func=FormBuilderMkText,ptext="height",helpText="height width",data="string")
                if height is None:
                    return
                elif height in ['d',]:
                    height=unit_registry.Quantity('1')
                else:
                    height=unit_registry.Quantity(height)
                break
            except Exception as e:
                print(e)
                try:
                    height=Control(func=FormBuilderMkText,ptext="height no units",helpText="height width, do not include units",data="dec.dec")
                    if height is None:
                        return
                    elif height in ['d',]:
                        height=decc(1)
                    break
                except Exception as e:
                    continue
        print(type(height),height,type(base))
        if isinstance(height,decimal.Decimal) and isinstance(base,decimal.Decimal):
            return decc((height*base)/decc(2))
        elif isinstance(height,pint.Quantity) and isinstance(base,pint.Quantity):
            return ((height.to(base)*base)/2)
        elif isinstance(height,pint.Quantity) and isinstance(base,decimal.Decimal):
            return ((height*unit_registry.Quantity(base,height.units))/2)
        elif isinstance(height,decimal.Decimal) and isinstance(base,pint.Quantity):
            return ((unit_registry.Quantity(height,base.units)*base)/2)

class Taxable:
    def general_taxable(self):
        taxables=[
"Alcoholic beverages",
"Books and publications",
"Cameras and film",
"Carbonated and effervescent water",
"Carbonated soft drinks and mixes",
"Clothing",
"Cosmetics",
"Dietary supplements",
"Drug sundries, toys, hardware, and household goods",
"Fixtures and equipment used in an activity requiring the holding of a seller’s permit, if sold at retail",
"Food sold for consumption on your premises (see Food service operations)",
"Hot prepared food products (see Hot prepared food products)",
"Ice",
"Kombucha tea (if alcohol content is 0.5 percent or greater by volume)",
"Medicated gum (for example, Nicorette and Aspergum)",
"Newspapers and periodicals",
"Nursery stock",
"Over-the-counter medicines (such as aspirin, cough syrup, cough drops, and throat lozenges)",
"Pet food and supplies",
"Soaps or detergents",
"Sporting goods",
"Tobacco products",
        ]
        nontaxables=[
"Baby formulas (such as Isomil)",
"Cooking wine",
"Energy bars (such as PowerBars)",
"""Food products—This includes baby food, artificial sweeteners, candy, gum, ice cream, ice cream novelties,
popsicles, fruit and vegetable juices, olives, onions, and maraschino cherries. Food products also include
beverages and cocktail mixes that are neither alcoholic nor carbonated. The exemption applies whether sold in
liquid or frozen form.""",
"Granola bars",
"Kombucha tea (if less than 0.5 percent alcohol by volume and naturally effervescent)",
"Sparkling cider",
"Noncarbonated sports drinks (including Gatorade, Powerade, and All Sport)",
"Pedialyte",
"Telephone cards (see Prepaid telephone debit cards and prepaid wireless cards)",
"Water—Bottled noncarbonated, non-effervescent drinking water",
        ]

        taxables_2=[
"Alcoholic beverages",
'''Carbonated beverages, including semi-frozen beverages
containing carbonation, such as slushies (see Carbonated fruit
juices)''',
"Coloring extracts",
"Dietary supplements",
"Ice",
"Over-the-counter medicines",
"Tobacco products",
"non-human food",
"Kombucha tea (if >= 0.5% alcohol by volume and/or is not naturally effervescent)",
        ]
        for i in taxables_2:
            if i not in taxables:
                taxables.append(i)

        ttl=[]
        for i in taxables:
            ttl.append(i)
        for i in nontaxables:
            ttl.append(i)
        htext=[]
        cta=len(ttl)
        ttl=sorted(ttl,key=str)
        for num,i in enumerate(ttl):
            htext.append(std_colorize(i,num,cta))
        htext='\n'.join(htext)
        while True:
            print(htext)
            select=Control(func=FormBuilderMkText,ptext="Please select all indexes that apply to item?",helpText=htext,data="list")
            if select is None:
                return
            for i in select:
                try:
                    index=int(i)
                    if ttl[index] in taxables:
                        return True
                except Exception as e:
                    print(e)
            return False
    def kombucha(self):
        '''determine if kombucha is taxable'''
        fd={
            'Exceeds 0.5% ABV':{
            'default':False,
            'type':'boolean',
            },
            'Is it Naturally Effervescent?':{
            'default':False,
            'type':'boolean',
            },

        }
        data=FormBuilder(data=fd)
        if data is None:
            return
        else:
            if data['Exceeds 0.5% ABV']:
                return True

            if not data['Is it Naturally Effervescent?']:
                return True

            return False
        
#tax rate tools go here
def AddNewTaxRate(excludes=['txrt_id','DTOE']):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        with Session(ENGINE) as session:
            '''AddNewTaxRate() -> None

            add a new taxrate to db.'''
            tr=TaxRate()
            session.add(tr)
            session.commit()
            session.refresh(tr)
            fields={i.name:{
            'default':getattr(tr,i.name),
            'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
            }

            fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
            if fd is None:
                session.delete(tr)
                return
            for k in fd:
                setattr(tr,k,fd[k])

        
            session.add(tr)
            session.commit()
            session.refresh(tr)
        print(tr)
        return tr.TaxRate

def GetTaxRate(excludes=['txrt_id','DTOE']):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        with Session(ENGINE) as session:
            '''GetTaxRate() -> TaxRate:Decimal

            search for and return a Decimal/decc
            taxrate for use by prompt.
            '''
            tr=TaxRate()
            fields={i.name:{
            'default':getattr(tr,i.name),
            'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
            }

            fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec} ; GetTaxRate Search -> ")
            if fd is None:
                return
            for k in fd:
                setattr(tr,k,fd[k])
            #and_
            filte=[]
            for k in fd:
                if fd[k] is not None:
                    if isinstance(fd[k],str):
                        filte.append(getattr(TaxRate,k).icontains(fd[k]))
                    else:
                        filte.append(getattr(tr,k)==fd[k])
        
            results=session.query(TaxRate).filter(and_(*filte)).all()
            ct=len(results)
            htext=[]
            for num,i in enumerate(results):
                m=std_colorize(i,num,ct)
                print(m)
                htext.append(m)
            htext='\n'.join(htext)
            if ct < 1:
                print(f"{Fore.light_red}There is nothing to work on in TaxRates that match your criteria.{Style.reset}")
                return
            while True:
                select=Control(func=FormBuilderMkText,ptext="Which index to return for tax rate[NAN=0.0000]?",helpText=htext,data="integer")
                print(select)
                if select is None:
                    return
                elif isinstance(select,str) and select.upper() in ['NAN',]:
                    return 0
                elif select in ['d',]:
                    return results[0].TaxRate
                else:
                    if index_inList(select,results):
                        return results[select].TaxRate
                    else:
                        continue

def price_by_tax(total=False):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        fields={
        'price':{
            'default':0,
            'type':'dec.dec'
            },
        'rate':{
            'default':GetTaxRate(),
            'type':'dec.dec'
            }
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec} ; Tax on Price ->")
        if fd is None:
            return
        else:
            price=fd['price']
            rate=fd['rate']
            if price is None:
                price=0
            if fd['rate'] is None:
                rate=0
            if total == False:
                return decc(price,cf=4)*decc(rate,cf=4)
            else:
                return (decc(price,cf=4)*decc(rate,cf=4))+decc(price,cf=4)

def price_plus_crv_by_tax(total=False):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        fields={
        'price':{
            'default':0,
            'type':'dec.dec'
            },
        'crv_total_for_pkg':{
            'default':0,
            'type':'dec.dec',
        },
        'rate':{
            'default':GetTaxRate(),
            'type':'dec.dec'
            }
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec};Tax on (Price+CRV)")
        if fd is None:
            return
        else:
            price=fd['price']
            rate=fd['rate']
            crv=fd['crv_total_for_pkg']
            if price is None:
                price=0
            if crv is None:
                crv=0
            if fd['rate'] is None:
                rate=0
            if total == False:
                return (decc(price,cf=4)+decc(crv,cf=4))*decc(rate,cf=4)
            else:
                return (price+crv)+((decc(price,cf=4)+decc(crv,cf=4))*decc(rate,cf=4))

def DeleteTaxRate(excludes=['txrt_id','DTOE']):
    with Session(ENGINE) as session:
        '''DeleteTaxRate() -> None

        search for and delete selected
        taxrate.
        '''
        '''AddNewTaxRate() -> None

        add a new taxrate to db.'''
        tr=TaxRate()
        fields={i.name:{
        'default':getattr(tr,i.name),
        'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
        }
        fd=FormBuilder(data=fields)
        if fd is None:
            return
        for k in fd:
            setattr(tr,k,fd[k])
        #and_
        filte=[]
        for k in fd:
            if fd[k] is not None:
                if isinstance(fd[k],str):
                    filte.append(getattr(TaxRate,k).icontains(fd[k]))
                else:
                    filte.append(getattr(tr,k)==fd[k])
        session.commit()
    
        results=session.query(TaxRate).filter(and_(*filte)).all()
        ct=len(results)
        htext=[]
        for num,i in enumerate(results):
            m=std_colorize(i,num,ct)
            print(m)
            htext.append(m)
        htext='\n'.join(htext)
        if ct < 1:
            print(f"{Fore.light_red}There is nothing to work on in TaxRates that match your criteria.{Style.reset}")
            return
        while True:
            select=Control(func=FormBuilderMkText,ptext="Which index to delete?",helpText=htext,data="integer")
            print(select)
            if select is None:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            elif isinstance(select,str) and select.upper() in ['NAN',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return 0
            elif select in ['d',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            else:
                if index_inList(select,results):
                    session.delete(results[select])
                    session.commit()
                    return
                else:
                    continue

def EditTaxRate(excludes=['txrt_id','DTOE']):
    '''DeleteTaxRate() -> None

    search for and delete selected
    taxrate.
    '''
    tr=TaxRate()
    fields={i.name:{
    'default':getattr(tr,i.name),
    'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
    }
    fd=FormBuilder(data=fields)
    if fd is None:
        return
    for k in fd:
        setattr(tr,k,fd[k])
    #and_
    filte=[]
    for k in fd:
        if fd[k] is not None:
            if isinstance(fd[k],str):
                filte.append(getattr(TaxRate,k).icontains(fd[k]))
            else:
                filte.append(getattr(tr,k)==fd[k])
    with Session(ENGINE) as session:
        results=session.query(TaxRate).filter(and_(*filte)).all()
        ct=len(results)
        htext=[]
        for num,i in enumerate(results):
            m=std_colorize(i,num,ct)
            print(m)
            htext.append(m)
        htext='\n'.join(htext)
        if ct < 1:
            print(f"{Fore.light_red}There is nothing to work on in TaxRates that match your criteria.{Style.reset}")
            return
        while True:
            select=Control(func=FormBuilderMkText,ptext="Which index to edit?",helpText=htext,data="integer")
            print(select)
            if select is None:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            elif isinstance(select,str) and select.upper() in ['NAN',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return 0
            elif select in ['d',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            else:
                if index_inList(select,results):
                    fields={i.name:{
                    'default':getattr(results[select],i.name),
                    'type':str(i.type).lower()} for i in results[select].__table__.columns if i.name not in excludes
                    }
                    fd=FormBuilder(data=fields)
                    for k in fd:
                        setattr(results[select],k,fd[k])
                    session.commit()
                    session.refresh(results[select])
                    print(results[select])
                    return
                else:
                    continue

def heronsFormula():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Calculate the semi-perimeter (s): Add the lengths of the three sides and divide by 2.
        s = (a + b + c) / 2
        '''
        fields={
            'side 1':{
            'default':1,
            'type':'dec.dec'
            },
            'side 2':{
            'default':1,
            'type':'dec.dec'
            },
            'side 3':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        s=(fd['side 1']+fd['side 2']+fd['side 3'])/2
        '''Apply Heron's formula: Substitute the semi-perimeter (s) and the side lengths (a, b, and c) into the formula:
        Area = √(s(s-a)(s-b)(s-c))'''
        Area=math.sqrt(s*(s-fd['side 1'])*(s-fd['side 2'])*(s-fd['side 3']))
        return Area

def volumeCylinderRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*(fd['radius']**2)*fd['height']
        return volume

def volumeCylinderDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*((fd['diameter']/2)**2)*fd['height']
        return volume

def volumeConeRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(1/3)*(Decimal(math.pi)*(fd['radius']**2)*fd['height'])
        return volume

def volumeConeDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(1/3)*(Decimal(math.pi)*((fd['diameter']/2)**2)*fd['height'])
        return volume

def volumeHemisphereRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(2/3)*Decimal(math.pi)*(fd['radius']**3)
        return volume

def volumeHemisphereDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(2/3)*Decimal(math.pi)*((fd['diameter']/2)**3)
        return volume

def areaCircleDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*((fd['diameter']/2)**2)
        return volume


def areaCircleRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*((fd['radius'])**2)
        return volume

###newest
def circumferenceCircleRadiu():
    #get the circumference of a circle using radius
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        2πr
        '''
        fields={
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        circumference=2*Deimal(math.pi)*fd['radius']
        return circumference

def circumferenceCircleDiameter():
    #get the circumference of a circle using diameter
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        2π(d/2)
        '''
        fields={
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        circumference=2*Deimal(math.pi)*Decimal(fd['diameter']/2)
        return circumference

def sudokuCandidates():
    #get the circumference of a circle using diameter
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        2π(d/2)
        '''
        gameSymbols=Control(func=FormBuilderMkText,ptext="Game symbols [123456789]",helpText="123456789",data="string")
        if gameSymbols in ['NaN',None,]:
            return
        elif gameSymbols in ['d',]:
            gameSymbols='123456789'

        fields={
            'Symbols for Row':{
            'default':'',
            'type':'string'
            },
            'Symbols for Column':{
            'default':'',
            'type':'string'
            },
            'Symbols for Cell':{
            'default':'',
            'type':'string'
            },
            'Symbols for Right-Diagnal':{
            'default':'',
            'type':'string'
            },
            'Symbols for Left-Diagnal':{
            'default':'',
            'type':'string'
            },
        }
        loop=True
        while loop:
            fd=FormBuilder(data=fields,passThruText=f"Sudoku Candidates? ")
            if fd is None:
                return
            
            sString=[]
            for i in fd:
                if isinstance(fd[i],str):
                    sString.append(fd[i])
            sString=' '.join(sString)
            cd=[]
            for i in gameSymbols:
                if i not in sString:
                    cd.append(i)
            print(cd)
            loop=Control(func=FormBuilderMkText,ptext="Again?",helpText="yes or no/boolean",data="boolean")
            if loop in ['NaN',None]:
                return
            elif loop in ['d',True]:
                loop=True
            else:
                return cd
'''
Ellipse: area=πab
, where 2a
 and 2b
 are the lengths of the axes of the ellipse.

Sphere: vol=4πr3/3
, surface area=4πr2
.

Cylinder: vol=πr2h
, lateral area=2πrh
, total surface area=2πrh+2πr2
.


Cone: vol=πr2h/3
, lateral area=πrr2+h2−−−−−−√
, total surface area=πrr2+h2−−−−−−√+πr2
'''

class candidates:
    def __new__(self,test=False):
        n=None
        symbols=[i for i in '123456789']
        none_symbol='0'

        if test:
            pzl={
            'l1':[1,n,9,n,n,3,7,n,8],
            'l2':[n,n,4,n,n,n,3,n,2],
            'l3':[3,n,5,n,6,8,1,9,4],
            'l4':[6,n,7,8,1,n,n,n,n],
            'l5':[9,3,1,n,n,n,5,8,n],
            'l6':[n,n,2,3,n,n,6,n,n],
            'l7':[n,n,8,n,n,5,n,3,n],
            'l8':[4,n,3,n,8,6,n,1,n],
            'l9':[n,9,6,n,n,n,n,n,7],
            }


        def mkpuzl():
            while True:
                done={}
                htext=[]
                symbols='123456789'
                ct=len(symbols)
                for num,i in enumerate(symbols):
                    htext.append(std_colorize(i,num,ct))
                    done[f'l{num+1}']={
                        'default':[],
                        'type':'list'
                    }
                finished=FormBuilder(data=done,passThruText=f"enter chars. of {symbols}, use 0 to represent an unfilled cell: Must be 9-Long")
                if finished is None:
                    return None
                else:
                    for i in finished:
                        if len(finished[i]) != 9:
                            continue
                        for num,ii in enumerate(finished[i]):
                            if ii == '0':
                                finished[i][num]=n
                    return finished


                #select a list of 9 symbols for ln#
                #symbol is 0, then symbol is None
                #append list to final list
                #for 9lines of 9elements per 1 line as a dict of 9 keys with 9 lists that are 9 elements long
        if not test:
            pzl=mkpuzl()

        while True:
            #print(pzl)
            if pzl is None:
                return
            mapped={
                'block1=':{
                    'rows':[0,1,2],
                    'columns':[0,1,2]
                },
                'block2':{
                    'rows':[0,1,2],
                    'columns':[3,4,5]
                },
                'block3':{
                    'rows':[0,1,2],
                    'columns':[4,5,6]
                },
                'block4':{
                    'rows':[3,4,5],
                    'columns':[0,1,2]
                },
                'block5':{
                    'rows':[3,4,5],
                    'columns':[3,4,5]
                },
                'block6':{
                    'rows':[3,4,5],
                    'columns':[6,7,8]
                },
                'block7':{
                    'rows':[6,7,8],
                    'columns':[0,1,2]
                },
                'block8':{
                    'rows':[6,7,8],
                    'columns':[3,4,5]
                },
                'block9':{
                    'rows':[6,7,8],
                    'columns':[6,7,8]
                },
            }

            def rx2idx(line,column,x_limit=9,y_limit=9):
                return ((x_limit*line)-(y_limit-column))

            def desired(block_x=[1,4],block_y=[1,4],num=''): 
                iblock_x=block_x
                iblock_x[-1]+=1

                iblock_y=block_y
                iblock_y[-1]+=1
                for i in range(*iblock_x):
                    for x in range(*iblock_y):
                        #print(f'block{num}',rx2idx(i,x))
                        yield rx2idx(i,x)
                        
            rgrid=[
            [[1,3],[1,3]],[[1,3],[4,6]],[[1,3],[7,9]],
            [[4,6],[1,3]],[[4,6],[4,6]],[[4,6],[7,9]],
            [[7,9],[1,3]],[[7,9],[4,6]],[[7,9],[7,9]],
            ]
            grid={}
            for num,y in enumerate(rgrid):
                grid[f'block{num+1}']=[i for i in desired(y[0],y[1],num+1)]

            #grid=mkgrid()
            def characters_row(row):
                tmp=''
                for i in row:
                    if i!=None:
                        tmp+=str(i)
                return tmp


            def characters_column(rows,column):
                tmp=''
                x=[]
                for r in rows:
                    c=rows[r][column]
                    if c is not None:
                        if not isinstance(c,list):
                            tmp+=str(c)
                return tmp

            def characters_block(pzl,mapped,ttl):
                tmp=''
                zz=[]
                for i in pzl:
                    zz.extend(pzl[i])
                ttl+=1
                #print(ttl,'ttl')
                for i in grid:
                    if ttl in grid[i]:
                        for x in grid[i]:
                            #print(x-1)
                            if zz[x-1] is not None:
                                tmp+=str(zz[x-1])
                            
                #back to the drawng board
                return tmp

            def display_candidates(pzl):
                ttl=0
                newStart=None
                while True:
                    ttl=0
                    for numRow in enumerate(pzl):
                        for COL in range(len(pzl[numRow[-1]])):
                            if ttl > 81:
                                ttl=0
                            filled=''
                            tmp=[]
                            ROW=[i for i in reversed(numRow)]
                            consumed=f"{characters_row(pzl[ROW[0]])}{characters_column(pzl,COL)}{characters_block(pzl,mapped,ttl)}"
                            tmpl=[]
                            for x in stre(consumed)/1:
                                if x not in tmpl:
                                    tmpl.append(x)
                            tmpl=sorted(tmpl)
                            fmsg=f'''Percent(({ttl}/80)*100)->{(ttl/80)*100:.2f} RowCol({Fore.orange_red_1}R={ROW[-1]},{Fore.light_steel_blue}C={COL})
    {Fore.light_green}Reduced("{consumed}")->"{''.join(tmpl)}"'''
                            symbol_string=f"""{fmsg}{Fore.light_yellow}
    NoneSymbol({none_symbol}){Fore.light_steel_blue}
    SYMBOL({pzl[numRow[-1]][COL]}) 
    ROWS({ROW[-1]}): {characters_row(pzl[ROW[0]])} 
    COLUMN({COL}): {characters_column(pzl,COL)} 
    BLOCK: '{characters_block(pzl,mapped,ttl)}' """
                            for char in symbols:
                                if char not in tmpl:
                                    tmp.append(char)
                            candidates=', '.join(tmp)
                            color=''
                            color_end=''
                            if len(candidates) == 1:
                                color=f"{Fore.light_green}"
                                color_end=f"{Style.reset}"
                                if pzl[numRow[-1]][COL] != candidates and pzl[numRow[-1]][COL] is not None:
                                    filled=f"{Fore.orange_red_1}AlreadyFilled({pzl[numRow[-1]][COL]}){Style.reset}"
                                    color_end=filled+color_end
                                    candidates=''
                            elif len(candidates) <= 0:
                                color=f"{Fore.light_red}"
                                if pzl[numRow[-1]][COL] is not None:
                                    filled=f"{Fore.orange_red_1}AlreadyFilled({pzl[numRow[-1]][COL]}){Style.reset}"
                                    color_end=filled+color_end
                                else:
                                    color_end=f"{filled} No candidates were found!{Style.reset}"
                            elif len(candidates) >= 1:
                                color=f"{Fore.light_cyan}"
                                color_end=f"{Style.reset}"
                                if pzl[numRow[-1]][COL] != candidates and pzl[numRow[-1]][COL] is not None:
                                    filled=f"{Fore.orange_red_1}AlreadyFilled({pzl[numRow[-1]][COL]}){Style.reset}"
                                    color_end=filled+color_end
                                    candidates=''
                            ttl+=1
                            if newStart is not None:
                                if ttl < newStart:
                                    continue
                                else:
                                    newStart=None
                            print(symbol_string)
                            print(f"{color}CANDIDATES: {color_end}",candidates)
                            
                            page=Control(func=lambda text,data:FormBuilderMkText(text,data,passThru=['goto',],PassThru=True),ptext="Next?",helpText="yes or no,",data="boolean")
                            if page in [None,'NaN']:
                                return
                            elif page in ['d',]:
                                pass
                            elif page in ['goto']:
                                breakMe=False
                                while True:
                                    stopAt=Control(func=FormBuilderMkText,ptext="Goto where?",helpText="0-81",data="integer")
                                    if stopAt in ['NaN',None]:
                                        return
                                    elif stopAt in [i for i in range(0,82)]:
                                        newStart=stopAt
                                        breakMe=True
                                        break
                                    else:
                                        print("between 0 and 81")
                                        continue
                                if breakMe:
                                    break

                            

                print('ROW and COL/COLUM are 0/zero-indexed!')
            display_candidates(pzl)
            control=Control(func=FormBuilderMkText,ptext="new data/nd,re-run/rr[default]",helpText='',data="string")
            if control in [None,'NaN']:
                return
            elif control in ['d','rr','re-run','re run']:
                continue
            elif control in ['new data','new-data','nd']:
                pzl=mkpuzl()
                continue
            else:
                continue


def costToRun():
    fields={
    'wattage of device plugged in, turned on/off?':{
        'default':60,
        'type':'float'
    },
    'hours of use?':{
        'default':1,
        'type':'float'
    },
    'electrical providers cost per kWh':{
        'default':0.70  ,
        'type':'float'
    },
    }

    fd=FormBuilder(data=fields)
    if fd is None:
        return
   
    cost=((fd['wattage of device plugged in, turned on/off?']/1000)*fd['electrical providers cost per kWh'])
    total_cost_to=cost*fd['hours of use?']
    return total_cost_to

def FederalIncomeTaxWithholding():
    fields={
    'Gross for Period':{
        'default':decc('657.88'),
        'type':'dec.dec'
    },
    f'IRS Publication 15-T ({datetime.now().year}) To Be Withheld for Status':{
        'default':decc('8'),
        'type':'dec.dec'
    },
    f'IRS Publication 15-T ({datetime.now().year}) WithHolding Amount "At Least" for Period':{
        'default':decc('655' ) ,
        'type':'dec.dec'
    },
    f'IRS Publication 15-T ({datetime.now().year}) WithHolding Amount "But Less Than" for Period':{
        'default':decc('660' ) ,
        'type':'dec.dec'
    },
    "Margin For Error":{
        'default':decc('0.05'),
        'type':'dec.dec'
    }
    }

    fd=FormBuilder(data=fields)
    if fd is None:
        return
   
    m=fd[f'IRS Publication 15-T ({datetime.now().year}) To Be Withheld for Status']/fd[f'IRS Publication 15-T ({datetime.now().year}) WithHolding Amount "At Least" for Period']
    mm=fd[f'IRS Publication 15-T ({datetime.now().year}) To Be Withheld for Status']/fd[f'IRS Publication 15-T ({datetime.now().year}) WithHolding Amount "But Less Than" for Period']
    mx=fd[f'IRS Publication 15-T ({datetime.now().year}) To Be Withheld for Status']/fd['Gross for Period']
    mmm=(m+mm+mx)/3
    gross=mmm*fd['Gross for Period']
    federal_withholding=gross+(gross*fd["Margin For Error"])

    return federal_withholding


def VAStateIncomeTaxWithholding():
    fields={
    'Gross for Period':{
        'default':decc('657.88'),
        'type':'dec.dec'
    },
    f'VA State Withholding ({datetime.now().year}) To Be Withheld for Status':{
        'default':decc('11'),
        'type':'dec.dec'
    },
    f'VA State Withholding ({datetime.now().year}) WithHolding Amount "At Least" for Period':{
        'default':decc('650' ) ,
        'type':'dec.dec'
    },
    f'VA State Withholding ({datetime.now().year}) WithHolding Amount "But Less Than" for Period':{
        'default':decc('660' ) ,
        'type':'dec.dec'
    },
    "Margin For Error":{
        'default':decc('0.0101'),
        'type':'dec.dec'
    }

    }

    fd=FormBuilder(data=fields)
    if fd is None:
        return
   
    m=fd[f'VA State Withholding ({datetime.now().year}) To Be Withheld for Status']/fd[f'VA State Withholding ({datetime.now().year}) WithHolding Amount "At Least" for Period']
    mm=fd[f'VA State Withholding ({datetime.now().year}) To Be Withheld for Status']/fd[f'VA State Withholding ({datetime.now().year}) WithHolding Amount "But Less Than" for Period']
    mx=fd[f'VA State Withholding ({datetime.now().year}) To Be Withheld for Status']/fd['Gross for Period']
    mmm=(m+mm+mx)/3
    gross=mmm*fd['Gross for Period']
    gross=gross+(gross*fd["Margin For Error"])
    return gross


def generic_service_or_item():
    fields={
    'PerBaseUnit':{
        'default':'squirt',
        'type':'string',
        },
    'PerBaseUnit_is_EquivalentTo[Conversion]':{
        'default':'1 squirt == 2 grams',
        'type':'string',
        },
    'PricePer_1_EquivalentTo[Conversion]':{
        'default':0,
        'type':'float',
        },
    'Name or Description':{
        'default':'dawn power wash',
        'type':'string'
        },
    'Cost/Price/Expense Taxed @ %':{
        'default':'Item was purchased for 3.99 Taxed @ 6.3% (PRICE+(PRICE+TAX))',
        'type':'string'
        },
    'Where was the item purchased/sold[Location/Street Address, City, State ZIP]?':{
        'default':'walmart in gloucester va, 23061',
        'type':'string'
        },
    }
    fd=FormBuilder(data=fields)
    if fd is not None:
        textty=[]
        cta=len(fd)
        for num,k in enumerate(fd):
            msg=f"{k} = '{fd[k]}'"
            textty.append(strip_colors(std_colorize(msg,num,cta)))
        master=f'''
Non-Std Item/Non-Std Service
----------------------------
{' '+'\n '.join(textty)}
----------------------------
        '''
        return master

def reciept_book_entry():
    fields={
    'reciept number':{
        'default':'',
        'type':'string'
    },
    'reciept dtoe':{
        'default':datetime.now(),
        'type':'datetime'
    },
    'recieved from':{
        'default':'',
        'type':'string'
    },
    'address':{
        'default':'',
        'type':'string'
    },
    'Amount ($)':{
        'default':0,
        'type':'dec.dec',
    },
    'For':{
        'default':'',
        'type':'string'
    },
    'By':{
        'default':'',
        'type':'string'
    },
    'Amount of Account':{
        'default':0,
        'type':'dec.dec',
    },
    'Amount Paid':{
        'default':0,
        'type':'dec.dec',
    },
    'Balance Due':{
        'default':0,
        'type':'dec.dec',
    },
    'Cash':{
        'default':0,
        'type':'dec.dec',
    },
    'Check':{
        'default':0,
        'type':'dec.dec',
    },
    'Money Order':{
        'default':0,
        'type':'dec.dec',
    },
    'Line 1':{
        'default':'',
        'type':'string'
    },
    'Line 2':{
        'default':'',
        'type':'string'
    },
    'Notes':{
        'default':'',
        'type':'string'
    },
    'Filing Location Id':{
        'default':'',
        'type':'string'
    },
    }
    fd=FormBuilder(data=fields)
    if fd is not None:
        textty=[]
        cta=len(fd)
        for num,k in enumerate(fd):
            msg=f"{k} = '{fd[k]}'"
            textty.append(strip_colors(std_colorize(msg,num,cta)))
        master=f'''
Reciept {fd['reciept number']}
----------------------------
{' '+'\n '.join(textty)}
----------------------------
        '''
        return master

def nowToPercentTime(now=None):
    if not isinstance(now,datetime):
        now=datetime.now()
    today=datetime(now.year,now.month,now.day)
    diff=now-today
    a=round(diff.total_seconds()/60/60/24,6)
    a100=round(a*100,2)
    m=str(now.strftime(f'{now} | %mM/%dD/%YY @ %H(24H)/%I %p(12H):%M:%S | {a100} Percent of 24H has passed since {today} as {diff.total_seconds()} seconds passed/{(24*60*60)} total seconds in day={a}*100={a100} | Percent of Day Passed = {a100}%'))
    return m


def ndtp():
    msg=''
    while True:
        try:
            fields={
                'distance':{
                'type':'float',
                'default':25,
                },
                'speed':{
                'type':'float',
                'default':70
                },
                'total break time':{
                'type':'string',
                'default':'10 minutes'
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            
            mph=fd['speed']
            distance=fd['distance']
            try:
                breaks=pint.Quantity(fd['total break time']).to('seconds').magnitude
            except Exception as e:
                breaks=pint.Quantity(fd['total break time']+' minutes').to('seconds').magnitude
            duration=pint.Quantity(distance/mph,'hour').to('sec').magnitude
            #12 minutes 
            buffer=timedelta(minutes=15)
            original=timedelta(seconds=duration)+timedelta(seconds=breaks)
            duration=timedelta(seconds=original.total_seconds()+buffer.total_seconds())
            now=datetime.now()
            then=now+duration
            msg=[]
            msg.append(f'Rate of Travel: {str(mph)}')
            msg.append(f'Distance To Travel: {distance}')
            msg.append(f"Now: {now}")
            msg.append(f'Non-Buffered Duration {original}')
            msg.append(f'Buffered: {duration} (+{buffer})')
            msg.append(f"Then: {then}")
            msg.append(f'Total Break Time: {timedelta(seconds=breaks)}')
            msg.append(f"From: {nowToPercentTime(now)}")
            msg.append(f"To: {nowToPercentTime(then)}")
            msg='\n\n'.join(msg)
            return msg
        except Exception as e:
            print(e)

def drug_text():
    while True:
        try:
            drug_names=[
            'thc flower',
            'thc vape',

            'thca flower',
            'thca vape',

            'caffiene',
            'caffiene+taurine',
            'caffiene+beta_alanine',

            'alcohol',
            'alcohol+thc flower',
            'alcohol+thca flower',
            
            'caffiene+thca flower+menthol',
            'caffiene+thc flower+menthol',
            ]
            extra_drugs=detectGetOrSet("extra_drugs","extra_drugs.csv",setValue=False,literal=True)
            if extra_drugs:
                extra_drugs=Path(extra_drugs)


                if extra_drugs.exists():
                    with extra_drugs.open("r") as fileio:
                        reader=csv.reader(fileio,delimiter=',')
                        for line in reader:
                            for sub in line:
                                if sub not in ['',]:
                                    sub=f"{sub} {Fore.light_green}[{Fore.cyan}{extra_drugs}{Fore.light_green}]{Fore.dark_goldenrod}"
                                    drug_names.append(sub)
                                    
            excludes_drn=['',' ',None,'\n','\r\n','\t',]
            rdr_state=db.detectGetOrSet('list maker lookup order',False,setValue=False,literal=False)
            if rdr_state:
                drug_names=list(sorted(set([i for i in drug_names if i not in excludes_drn]),key=str))
            else:
                drug_names=list(reversed(sorted(set([i for i in drug_names if i not in excludes_drn]),key=str)))
            htext=[]
            cta=len(drug_names)
            for num,i in enumerate(drug_names):
                htext.append(std_colorize(i,num,cta))
            htext='\n'.join(htext)
            
            which=Control(func=FormBuilderMkText,ptext=f"{htext}\n{Fore.yellow}which index?",helpText=htext,data="integer")
            if which in [None,'NaN']:
                return

            return strip_colors(drug_names[which])
        except Exception as e:
            print(e)
            continue

def TotalCurrencyFromMass():
    msg=''
    while True:
        try:
            fields={
                '1 Unit Mass(Grams)':{
                'type':'dec.dec',
                'default':2.50,
                },
                '1 Unit Value($)':{
                'type':'dec.dec',
                'default':0.01
                },
                'Total Unit Mass (Total Coin/Bill Mass)':{
                'type':'dec.dec',
                'default':0.0
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            value=(decc(1/fd['1 Unit Mass(Grams)'])*decc(fd['1 Unit Value($)']))*decc(fd['Total Unit Mass (Total Coin/Bill Mass)'])
            return value
        except Exception as e:
            print(e)

def BaseCurrencyValueFromMass():
    msg=''
    while True:
        try:
            fields={
                '1 Unit Mass(Grams)':{
                'type':'dec.dec',
                'default':2.50,
                },
                '1 Unit Value($)':{
                'type':'dec.dec',
                'default':0.01
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            value=(decc(1/fd['1 Unit Mass(Grams)'])*decc(fd['1 Unit Value($)']))
            return value
        except Exception as e:
            print(e)


def USCurrencyMassValues():
    while True:
        try:
            drug_names={
            'Mass(Grams) - 1 Dollar Coin/1.0':decc(8.1),
            'Mass(Grams) - Half Dollar/0.50':decc(11.340),
            'Mass(Grams) - Quarter/0.25':decc(5.670),
            'Mass(Grams) - Nickel/0.05':decc(5.0),
            'Mass(Grams) - Dime/0.10':decc(2.268),
            'Mass(Grams) - Penny/0.01':decc(2.5),
            'Mass(Grams) - Bill($1/$2/$5/$10/$20/$50/$100':decc(1),

            'Value for Mass(Grams) - 1 Dollar Coin/8.1 Grams':1.00,
            'Value for Mass(Grams) - Half Dollar/11.340 Grams':0.50,
            'Value for Mass(Grams) - Quarter/5.670 Grams':0.25,
            'Value for Mass(Grams) - Nickel/5 Grams':0.05,
            'Value for Mass(Grams) - Dime/2.268 Grams':0.10,
            'Value for Mass(Grams) - Penny/2.5 Grams':0.01,
            'Value for Mass(Grams) - 1$ Bill/1 Grams':1,
            'Value for Mass(Grams) - 2$ Bill/1 Grams':2,
            'Value for Mass(Grams) - 5$ Bill/1 Grams':5,
            'Value for Mass(Grams) - 10$ Bill/1 Grams':10,
            'Value for Mass(Grams) - 20$ Bill/1 Grams':20,
            'Value for Mass(Grams) - 50$ Bill/1 Grams':50,
            'Value for Mass(Grams) - 100$ Bill/1 Grams':100,
            }
            

            keys=[]
            htext=[]
            cta=len(drug_names)
            for num,i in enumerate(drug_names):
                msg=f'{i} -> {drug_names[i]}'
                htext.append(std_colorize(msg,num,cta))
                keys.append(i)
            htext='\n'.join(htext)
            print(htext)
            which=Control(func=FormBuilderMkText,ptext="which index?",helpText=htext,data="integer")
            if which in [None,'NaN']:
                return
            return drug_names[keys[which]]
            
        except Exception as e:
            print(e)
            continue


def golden_ratio():
    msg=''
    while True:
        try:
            fields={
                'measurement':{
                'type':'dec.dec',
                'default':48,
                },
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            side1_value=(decc(fd['measurement'])/decc(scipy.constants.golden_ratio))
            side2_value=fd['measurement']-decc(side1_value)
            which=Control(func=FormBuilderMkText,ptext=f"Which side do you wish to return [for a side of {fd['measurement']}: side1_value={side1_value},side2_value={side2_value}]?",helpText="yes/1/true=side 1,side 2 is false/no/0",data="boolean")
            if which in [None,"NaN"]:
                return
            elif which:
                return side1_value
            else:
                return side2_value
        except Exception as e:
            print(e)


def currency_conversion():
    cvt_registry=pint.UnitRegistry()
    
    definition=f'''
    USD = [currency]
Argentine_Peso  =    nan usd
Australian_Dollar   =    nan usd
Bahraini_Dinar  =    nan usd
Botswana_Pula   =    nan usd
Brazilian_Real  =    nan usd
British_Pound   =    nan usd
Bruneian_Dollar =    nan usd
Bulgarian_Lev   =    nan usd
Canadian_Dollar =    nan usd
Chilean_Peso    =    nan usd
Chinese_Yuan_Renminbi   =    nan usd
Colombian_Peso  =    nan usd
Czech_Koruna    =    nan usd
Danish_Krone    =    nan usd
Emirati_Dirham  =    nan usd
Euro    =    nan usd
Hong_Kong_Dollar    =    nan usd
Hungarian_Forint    =    nan usd
Icelandic_Krona =    nan usd
Indian_Rupee    =    nan usd
Indonesian_Rupiah   =    nan usd
Iranian_Rial    =    nan usd
Israeli_Shekel  =    nan usd
Japanese_Yen    =    nan usd
Kazakhstani_Tenge   =    nan usd
Kuwaiti_Dinar   =    nan usd
Libyan_Dinar    =    nan usd
Malaysian_Ringgit   =    nan usd
Mauritian_Rupee =    nan usd
Mexican_Peso    =    nan usd
Nepalese_Rupee  =    nan usd
New_Zealand_Dollar  =    nan usd
Norwegian_Krone =    nan usd
Omani_Rial  =    nan usd
Pakistani_Rupee =    nan usd
Philippine_Peso =    nan usd
Polish_Zloty    =    nan usd
Qatari_Riyal    =    nan usd
Romanian_New_Leu    =    nan usd
Russian_Ruble   =    nan usd
Saudi_Arabian_Riyal =    nan usd
Singapore_Dollar    =    nan usd
South_African_Rand  =    nan usd
South_Korean_Won    =    nan usd
Sri_Lankan_Rupee    =    nan usd
Swedish_Krona   =    nan usd
Swiss_Franc =    nan usd
Taiwan_New_Dollar   =    nan usd
Thai_Baht   =    nan usd
Trinidadian_Dollar  =    nan usd
Turkish_Lira    =    nan usd

@context FX
Argentine_Peso  =    0.000671    usd
Australian_Dollar   =    0.651104    usd
Bahraini_Dinar  =    2.659574    usd
Botswana_Pula   =    0.070042    usd
Brazilian_Real  =    0.185537    usd
British_Pound   =    1.330948    usd
Bruneian_Dollar =    0.769854    usd
Bulgarian_Lev   =    0.594475    usd
Canadian_Dollar =    0.714527    usd
Chilean_Peso    =    0.001062    usd
Chinese_Yuan_Renminbi   =    0.140424    usd
Colombian_Peso  =    0.000259    usd
Czech_Koruna    =    0.047793    usd
Danish_Krone    =    0.155642    usd
Emirati_Dirham  =    0.272294    usd
Euro    =    1.162692    usd
Hong_Kong_Dollar    =    0.128701    usd
Hungarian_Forint    =    0.002981    usd
Icelandic_Krona =    0.008119    usd
Indian_Rupee    =    0.011384    usd
Indonesian_Rupiah   =    0.00006 usd
Iranian_Rial    =    0.000024    usd
Israeli_Shekel  =    0.304734    usd
Japanese_Yen    =    0.006545    usd
Kazakhstani_Tenge   =    0.00186 usd
Kuwaiti_Dinar   =    3.261214    usd
Libyan_Dinar    =    0.183824    usd
Malaysian_Ringgit   =    0.236753    usd
Mauritian_Rupee =    0.02197 usd
Mexican_Peso    =    0.054181    usd
Nepalese_Rupee  =    0.007112    usd
New_Zealand_Dollar  =    0.575051    usd
Norwegian_Krone =    0.099905    usd
Omani_Rial  =    2.603489    usd
Pakistani_Rupee =    0.003531    usd
Philippine_Peso =    0.017016    usd
Polish_Zloty    =    0.274017    usd
Qatari_Riyal    =    0.274725    usd
Romanian_New_Leu    =    0.228593    usd
Russian_Ruble   =    0.012559    usd
Saudi_Arabian_Riyal =    0.266667    usd
Singapore_Dollar    =    0.769854    usd
South_African_Rand  =    0.057932    usd
South_Korean_Won    =    0.000695    usd
Sri_Lankan_Rupee    =    0.003293    usd
Swedish_Krona   =    0.106347    usd
Swiss_Franc =    1.256685    usd
Taiwan_New_Dollar   =    0.032417    usd
Thai_Baht   =    0.030604    usd
Trinidadian_Dollar  =    0.147095    usd
Turkish_Lira    =    0.023829    usd
@end'''.lower()
    defFile=db.detectGetOrSet("currency_definitions_file","currency_definitions.txt",setValue=False,literal=True)
    if defFile is None:
        return
    defFile=Path(defFile)
    with open(defFile,"w") as out:
        out.write(definition)
    cvt_registry.load_definitions(defFile)
    with cvt_registry.context("fx") as cvtr:  
        while True:  
            try:
                htext=[]
                definition=definition.split("@context FX")[-1].replace('\n@end','')
                cta=len(definition.split("\n"))
                formats='\n'.join([std_colorize(i,num,cta) for num,i in enumerate(definition.split("\n"))])
                
                formats=f'''Conversion Formats are:\n{formats}\n'''
                fields={
                'value':{
                    'default':1,
                    'type':'float',
                },
                'FromString':{
                    'default':'USD',
                    'type':'string',
                },
                'ToString':{
                    'default':'Euro',
                    'type':'string'
                },
                }
                fb=FormBuilder(data=fields,passThruText=formats)
                if fb is None:
                    return

                return_string=fb['ToString'].lower()
                value_string=f"{fb['value']} {fb['FromString']}".lower()
                resultant=cvtr.Quantity(value_string).to(return_string)

                #if it gets here return None
                return resultant
            except Exception as e:
                print(e)

def bible_try():
    try:
        os.system("sonofman")
        return None
    except Exception as e:
        print(e)

DELCHAR=db.detectGetOrSet("DELCHAR preloader func","|",setValue=False,literal=True)
if not DELCHAR:
    DELCHAR='|'

def SalesFloorLocationString():
    fields=OrderedDict({

        'Aisle[s]':{
            'default':'',
            'type':'string',
        },
        'Bay[s]/AisleDepth':{
            'default':'',
            'type':'string',
        },
        'Shel[f,ves]':{
            'default':'',
            'type':'string',
        }
    })
    passThruText=f"""
{Fore.orange_red_1}Valid Aisle[s]:{Fore.grey_85}
    this is the aisle on which the product resides
    if the product belongs on an end cap use the endcap here as
    well. endcaps are numbered 0+=1 from left to right of the store
    front. the same is true for aisle. if the product resides on an 
    end cap, append FEC (0FEC) to signify front end cap 0, or 0REC for 
    rear end cap 0.
    0 -> on aisle 0
    0,1 -> on aisle 0 and  1
    0-2 -> from aisle 0 to aisle 2

    encaps on the front side of the aisle will have an FEC Appended to its number
     The same is true for rear of the aisle(REC). if a encap range is used, the character
     will identify its side of the store. if two encaps on opposite sides of the store
     are specified, then use 2 separate ranges; one for front and one for the rear.
    0FEC -> on front endcap 0
    0FEC,1REC -> on front endcap 0 and on rear endcap 1.
    0-2FEC -> from front endcap 0 to front endcap 2
    0-2REC -> from rear endcap 0 to rear endcap 2
    0-2FEC,0-2REC -> from front endcap 0 to front endcap 2 && from rear endcap 0 to rear endcap 2

    if No number is provided, but a common NAME is used, use that here for this section of the location.
{Fore.orange_red_1}Valid 'Bay[s]/AisleDepth':{Fore.grey_85}
    This is How many shelf bays deep from the front of the store
     to the back, where 0 is the first bay from the endcap at the 
     front of the store and increments upwards to the rear end cap.
     Bays on the right side of the aisle will have an R Appended to its number
     The same is true for left of the aisle. if a bay range is used, the character
     will identify its side of the aisle. if two bays on opposite sides of the aisle
     are specified, then use 2 separate ranges; one for left and one for right.
    0 -> on bay 0
    0,1 -> on bay 0 and  1
    0-2R -> from bay 0 to bay 2 on the right side of the aisle
    0-2L -> from bay 0 to bay 2 on the left side of the aisle
    0-2R,0-2L -> from bay 0 to bay 2 on the right side of the aisle && from bay 0 to bay 2 on the left side of the aisle.

    if No number is provided, but a common NAME is used, use that here for this section of the location.    
{Fore.orange_red_1}Valid Shel[f,ves]:{Fore.grey_85}
    this is the height where the product is on the shelf
    shelves are number 0 to their highest from bottom to top
    where the very bottom shelf is 0, and the next following shelf upwards is 
    1, and so on.
    0 -> on shelf 0
    0,1 -> on shelf 0 and  1
    0-2 -> from shelf 0 to shelf 2

    if No number is provided, but a common NAME is used, use that here for this section of the location.    
{Fore.light_green}Aisle or EndCap{Fore.light_red}/{Fore.light_yellow}Depth or Bay in Aisle{Fore.light_red}/{Fore.light_steel_blue}Shelf or Location Number(s) Where Item Resides [optional]{Style.reset}
{Fore.light_green}A completely Valid Example is Aisle 0|Household Chemicals|Kitchen Care, which is where Dawn Dish Detergent is normally located.
{Fore.light_red}{os.get_terminal_size().columns*'/'}
"""
    fb=FormBuilder(data=fields,passThruText=passThruText)
    if fb is None:
        return
    if fb['Shel[f,ves]'] not in ['',]:
        fb['Shel[f,ves]']=f"{DELCHAR}{fb['Shel[f,ves]']}"
    locationString=f"{fb['Aisle[s]']}{DELCHAR}{fb['Bay[s]/AisleDepth']}{fb['Shel[f,ves]']}"
    return locationString

def BackroomLocation():
    fields=OrderedDict({
        'moduleType':{
            'default':'',
            'type':'string',
            },
        'moduleNumberRange':{
            'default':'',
            'type':'string',
        },
        'caseID':{
            'default':'',
            'type':'string',
        },

    })
    passThruText=f'''
{Fore.orange_red_1}Valid ModuleTypes:{Fore.grey_85}
    this what to look on for where the product is stored
    s or S -> For Pallet/Platform [General]/Skid
    u or U -> For U-Boat/Size Wheeler
    rc or rC or Rc or RC ->  for RotaCart
    sc or sC or Sc or SC -> Shopping Cart
    if a name is used, or common identifier is used, use that here in this segment of the location.

{Fore.orange_red_1}Valid ModuleNumberRange:{Fore.grey_85}
    This which of the what's contains said item.
    0 -> on which 0
    0,1 -> on which 0 and which 1
    0-2 -> from which 0 to which 2 on the left side of the aisle
    if a name is used, or common identifier is used, use that here in this segment of the location.
{Fore.orange_red_1}Valid caseID:{Fore.grey_85}
    This is the case where the item is stored in which is the which found on the what.
    anything that you want as long as it is unique to the module in which it is stored.
     try using the following cmds for something on the fly.
     nanoid - nanoid
     crbc - checked random barcode
     dsur - generate a datestring
     urid - generate reciept id with a log
     cruid - checked uuid
     if a name is used, or common identifier is used, use that here in this segment of the location.
{Fore.light_red}{os.get_terminal_size().columns*'/'}

    '''
    fb=FormBuilder(data=fields,passThruText=passThruText)
    if fb is None:
        return
    if fb['caseID'] not in ['',]:
        fb['caseID']=f"{DELCHAR}{fb['caseID']}"
    locationString=f"{fb['moduleType']}{DELCHAR}{fb['moduleNumberRange']}{' '.join(db.stre(fb['caseID'])/3)}"
    return locationString

def TaxMuleFraud():
    msg=''
    while True:
        try:
            fields={
                'Price':{
                'type':'dec.dec',
                'default':decc(2.50,)
                },
                'Legally Applied Tax':{
                'type':'dec.dec',
                'default':decc(0.01)
                },
                'Mule Tax Rate (Charged as Despite being legally the other)':{
                'type':'dec.dec',
                'default':decc(0.063)
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
                
            prc=fd['Price']
            ltx=fd['Legally Applied Tax']
            iltx=fd['Mule Tax Rate (Charged as Despite being legally the other)']
            print(BooleanAnswers.FraudAlert)
            totals={
            f'legally_taxed_tax[(Price({prc})*legal_tax({ltx})]':fd['Price']*fd['Legally Applied Tax'],
            f'legally_taxed_price[Price({prc})+(Price({prc})*legal_tax({ltx})]':(fd['Price']*fd['Legally Applied Tax'])+fd['Price'],

            f'illegally_taxed_tax[Price({prc})*Illegal Tax({iltx})]':fd['Price']*fd['Mule Tax Rate (Charged as Despite being legally the other)'],
            f'illegally_taxed_price(What was charged to the customer)[Price({prc})+(Price({prc})*Illegal_tax({iltx}))]':(fd['Price']*fd['Mule Tax Rate (Charged as Despite being legally the other)'])+fd['Price'],

            f'fraud_profit_tax_only[Price({prc})*(illegal_tax({iltx})-legal_tax({ltx})]':fd['Price']*(fd['Mule Tax Rate (Charged as Despite being legally the other)']-fd['Legally Applied Tax']),
            f'fraud_profit_as_price[Price({prc})+(Price({prc})*(illegal_tax({iltx})-legal_tax({ltx}))]':(fd['Price']*(fd['Mule Tax Rate (Charged as Despite being legally the other)']-fd['Legally Applied Tax']))+fd['Price'],
            }
            cta=len(totals)
            htext='\n'.join([std_colorize(f'{i} = {Fore.light_green}{totals[i]}',num,cta) for num,i in enumerate(totals)])
            while True:
                which=Control(func=FormBuilderMkText,ptext=f"{htext}\nwhich index to return?",helpText=htext,data="integer")
                if which in [None,'NaN']:
                    return 
                elif which in range(0,len(totals)):
                    return totals[[i for i in totals.keys()][which]]
                else:
                    continue

            value=None

            return value
        except Exception as e:
            print(e)

def abstract_filter(model):
    #still needs <=,>=,!=,<,>,
    #use +-10~=$VAL for around 10+- the value $VAL
    prototype=model()
    try:
        setattr(prototype,'photoSerialNo',None)
    except Exception as e:
        print(e)
    fields={i.name:{'default':getattr(prototype,i.name),'type':str(i.type).lower()} for i in prototype.__table__.columns}
    fields.pop('dtoe')
    fb=FormBuilder(data=fields)
    if not fb:
        return []
    xfilter=[]
    print(xfilter)

    for k in fb:
        data=fb[k]
        print(data,k)
        if data is not None:
            if isinstance(data,datetime):
                xfilter.append(getattr(model,k)==data)
            elif isinstance(data,str):
                xfilter.append(getattr(model,k).icontains(data))
            elif isinstance(data,int):
                xfilter.append(getattr(model,k)==data)
            elif isinstance(data,float):
                xfilter.append(getattr(model,k)==data)
    if len(xfilter) < 1:
        return None
    return or_(and_(*xfilter),or_(*xfilter))

class BTemplate:
    def __str__(self):
        return f"{Fore.light_yellow}{self.__class__.__name__}(){Fore.light_green} exited {Fore.orange_red_1}@{Fore.dark_goldenrod} {datetime.now()}{Fore.orange_red_1}!"

    def __repr__(self):
        return self.__str__()

class Templogger(BTemplate):
    def fix_table(self):
        TemplLog.__table__.drop(ENGINE)
        TemplLog.metadata.create_all(ENGINE)
        print("Done!")


    def newLog(self,temp=None):
        if temp:
            arg=True
        else:
            arg=False
        with Session(ENGINE) as session:
            excludes=['templogid',]
            provided=False
            print(temp)
            if temp is None:
                temp=TemplLog()
            else:
                provided=True

            if not provided:
                session.add(temp)
                session.commit()
                session.refresh(temp)
            else:
                temp=session.query(TemplLog).filter(TemplLog.templogid==temp.templogid).first()
            print(temp)

            fields={str(i.name):{'default':getattr(temp,i.name),'type':str(i.type).lower()} for i in temp.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(temp)
                session.commit()
                return
            for k in fb:
                setattr(temp,k,fb[k])
            temp.dtoe=datetime.now()
            session.commit()
            session.refresh(temp)
            print(temp)
            return temp

    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''
        for xnum,i in enumerate(data):
            processed_templerature_string=pint.Quantity(i.templerature_value,i.templerature_unit)
            msg=f"""TemplLog ->\n {ii}    
{Fore.light_red}[{Fore.cyan}templogid{Fore.light_red}] {Fore.light_green}{i.templogid}
{Fore.light_red}[{Fore.cyan}dtoe{Fore.light_red}] {Fore.light_green}{i.dtoe}
{Fore.light_red}[{Fore.cyan}Logged{Fore.light_yellow} Temperature{Fore.light_red}] {Fore.light_green}{processed_templerature_string.to('degC')} {Fore.green_yellow}or {processed_templerature_string.to('degF')} {Fore.light_magenta}or {processed_templerature_string.to('degK')}
{Fore.light_red}[{Fore.cyan}Location{Fore.light_red}] {Fore.light_green}{i.Location}
{Fore.light_red}[{Fore.cyan}EmployeeIDorNAME{Fore.light_red}] {Fore.light_green}{i.EmployeeIDorNAME}
{Fore.light_red}[{Fore.cyan}note{Fore.light_red}] {Fore.light_green}{i.note}{Style.reset}
            """
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(TemplLog).filter(TemplLog.templogid==item.templogid).first()
                return self.newLog(temp=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(TemplLog).filter(TemplLog.templogid==item.templogid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            
            filt=abstract_filter(TemplLog)
            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                return
            if filt is not None:
                query=session.query(TemplLog).filter(filt)
            else:
                query=session.query(TemplLog)
            
            
            orderedQuery=orderQuery(query,TemplLog.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()

            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)



    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            }
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}Templogger {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")


class MPGLogger(BTemplate):
    def fix_table(self):
        MPGL.__table__.drop(ENGINE)
        MPGL.metadata.create_all(ENGINE)
        print("Done!")


    def newLog(self,mpgl=None):
        if mpgl:
            arg=True
        else:
            arg=False

        with Session(ENGINE) as session:
            excludes=['mpglid',]
            provided=False
            #print(mpgl,"#0")
            if mpgl is None:
                mpgl=MPGL()
            else:
                provided=True

            if not provided:
                session.add(mpgl)
                session.commit()
                session.refresh(mpgl)
            else:
                mpgl=session.query(MPGL).filter(MPGL.mpglid==mpgl.mpglid).first()
            #print(mpgl,'#1')

            fields={str(i.name):{'default':getattr(mpgl,i.name),'type':str(i.type).lower()} for i in mpgl.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(mpgl)
                session.commit()
                return
            for k in fb:
                setattr(mpgl,k,fb[k])
            mpgl.dtoe=datetime.now()
            session.commit()
            session.refresh(mpgl)
            #print(mpgl,'#2')
            return mpgl

    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''
        for xnum,i in enumerate(data):
            dist=0
            mpg=0
            fuelused=0
            if i.Starting_Odometer_Reading is not None and i.Ending_Odometer_Reading is not None:
                dist=unit_registry.Quantity(i.Ending_Odometer_Reading,i.Odometer_Unit_Of_Distance)-unit_registry.Quantity(i.Starting_Odometer_Reading,i.Odometer_Unit_Of_Distance)
                if i.FuelUsed:
                    fuelused=unit_registry.Quantity(i.FuelUsed,i.FuelUsedUnit)
                    mpg=dist/fuelused
                    
            
            msg=f"""{Back.black}MPG Log {i.LicensePlateOrVehicleIdentifier}[dtoe={i.dtoe}/comment='{i.comment}']->
{Fore.light_steel_blue}LicensePlateOrVehicleIdentifier{Fore.light_red}: {Fore.dark_goldenrod}{i.LicensePlateOrVehicleIdentifier}{Style.reset}
{Fore.light_green}Starting Odometer Reading{Fore.light_yellow}:{Fore.light_red} {i.Starting_Odometer_Reading}{Style.reset}
{Fore.light_green}Ending Odometer Reading{Fore.light_yellow}:{Fore.light_red} {i.Ending_Odometer_Reading}{Style.reset}
{Fore.light_green}Distance Travelled({Fore.light_cyan}End-Start{Fore.light_yellow}){Fore.light_yellow}:{Fore.light_red} {dist}{Style.reset}
{Fore.light_green}Unit Of Distance{Fore.light_yellow}:{Fore.light_red} {i.Odometer_Unit_Of_Distance}{Style.reset}
{Fore.light_green}Fuel-Used({Fore.light_cyan}What you refueled at the pump{Fore.light_yellow}){Fore.light_yellow}:{Fore.light_red} {fuelused}{Style.reset}
{Fore.light_green}Unit of Volume for Fuel Used{Fore.light_yellow}:{Fore.light_red} {i.FuelUsedUnit}{Style.reset}
{Fore.light_green}{i.Odometer_Unit_Of_Distance}-Per-{i.FuelUsedUnit}({Fore.light_cyan}Distance/FuelUsed{Fore.light_yellow}){Fore.light_yellow}:{Fore.light_red} {mpg}{Style.reset}
            """
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(MPGL).filter(MPGL.mpglid==item.mpglid).first()
                return self.newLog(mpgl=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(MPGL).filter(MPGL.mpglid==item.mpglid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            filt=abstract_filter(MPGL)

            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                return
            if filt is not None:
                query=session.query(MPGL).filter(filt)
            else:
                query=session.query(MPGL)
            
           
            orderedQuery=orderQuery(query,MPGL.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            '''
            orderedQuery=orderQuery(query,FuelPrice.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()
            '''

            results=limited.all()
            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)



    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 1'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 2'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 3'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 4'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            }
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}MPGL/Miles Per Gallon Logger: {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")


class GasLogger(BTemplate):
    

    def fix_table(self):
        FuelPrice.__table__.drop(ENGINE)
        FuelPrice.metadata.create_all(ENGINE)
        print("Done!")


    def newLog(self,fuel=None):
        if fuel:
            arg=True
        else:
            arg=False

        with Session(ENGINE) as session:
            excludes=['fuelid',]
            provided=False
            #print(fuel,"#0")
            if fuel is None:
                fuel=FuelPrice()
            else:
                provided=True

            if not provided:
                session.add(fuel)
                session.commit()
                session.refresh(fuel)
            else:
                fuel=session.query(FuelPrice).filter(FuelPrice.fuelid==fuel.fuelid).first()
            #print(fuel,'#1')

            fields={str(i.name):{'default':getattr(fuel,i.name),'type':str(i.type).lower()} for i in fuel.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(fuel)
                session.commit()
                return
            for k in fb:
                setattr(fuel,k,fb[k])
            fuel.dtoe=datetime.now()
            session.commit()
            session.refresh(fuel)
            #print(fuel,'#2')
            return fuel

    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''
        for xnum,i in enumerate(data):
            dist=0
            mpg=0
            fuelused=0
            msg=f"""
            {Fore.orange_red_1}Location: {Fore.light_yellow}{i.location}
            {Fore.orange_red_1}Address[{Fore.light_steel_blue}not applicable if location is different or otherwise specified{Fore.orange_red_1}]:{Fore.grey_85}{i.street_address}, {i.city_county_of}, {i.state} {i.zipcode}, {i.country}
            {Fore.light_steel_blue}DTOE: {i.dtoe}
            {Fore.light_cyan}Comment:{i.comment}
            {Fore.light_green}{i.fuel_name}{Fore.light_red} @ {Fore.light_yellow}{i.fuel_price} {Fore.light_green}{i.fuel_price_unit}{Style.reset}
            """
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(FuelPrice).filter(FuelPrice.fuelid==item.fuelid).first()
                return self.newLog(fuel=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(FuelPrice).filter(FuelPrice.fuelid==item.fuelid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            filt=abstract_filter(FuelPrice)

            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                return
            if filt is not None:
                query=session.query(FuelPrice).filter(filt)
            else:
                query=session.query(FuelPrice)

            orderedQuery=orderQuery(query,FuelPrice.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()
            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)



    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 1'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 2'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 3'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 4'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            }
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}Fuel Price Logger: {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")

def QtyString():
    msg=''
    while True:
        try:
            fields={
                'Barcode':{
                'type':'string',
                'default':'',
                },
                'qty':{
                'type':'dec.dec',
                'default':decc('0001.0000')
                },
                'qtyUnit':{
                'type':'string',
                'default':'Unit/Each'
                },
                'dtoe':{
                'type':'datetime',
                'default':datetime.now()
                },
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
                
            

            value=f"{fd['Barcode']}|{fd['qty']}|{fd['qtyUnit']}|{fd['dtoe']}"

            return value
        except Exception as e:
            print(e)
'''
class DoorSealRegistryLogger(BTemplate):
    def __new__(self):
        return "Not Yet Ready!"

'''


class DoorSealRegistryLogger(BTemplate):
    

    def fix_table(self):
        DoorSealRegistry.__table__.drop(ENGINE)
        DoorSealRegistry.metadata.create_all(ENGINE)
        print("Done!")


    def newLog(self,doorSealRegistry=None):
        if doorSealRegistry:
            arg=True
        else:
            arg=False

        with Session(ENGINE) as session:
            excludes=['dsrid',]
            provided=False
            #print(doorSealRegistry,"#0")
            if doorSealRegistry is None:
                doorSealRegistry=DoorSealRegistry()
            else:
                provided=True

            if not provided:
                session.add(doorSealRegistry)
                session.commit()
                session.refresh(doorSealRegistry)
            else:
                doorSealRegistry=session.query(doorSealRegistry).filter(doorSealRegistry.dsrid==doorSealRegistry.dsrid).first()
            #print(doorSealRegistry,'#1')

            fields={str(i.name):{'default':getattr(doorSealRegistry,i.name),'type':str(i.type).lower()} for i in doorSealRegistry.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(doorSealRegistry)
                session.commit()
                return
            for k in fb:
                setattr(doorSealRegistry,k,fb[k])
            doorSealRegistry.dtoe=datetime.now()
            session.commit()
            session.refresh(doorSealRegistry)
            #print(doorSealRegistry,'#2')
            return doorSealRegistry


    def newLog(self,door_seal_log_registry=None):
        if door_seal_log_registry:
            arg=True
        else:
            arg=False
        with Session(ENGINE) as session:
            excludes=['dsrid',]
            provided=False
            print(door_seal_log_registry)
            if door_seal_log_registry is None:
                door_seal_log_registry=DoorSealRegistry()
            else:
                provided=True

            if not provided:
                session.add(door_seal_log_registry)
                session.commit()
                session.refresh(door_seal_log_registry)
            else:
                door_seal_log_registry=session.query(DoorSealRegistry).filter(DoorSealRegistry.dsrid==door_seal_log_registry.dsrid).first()
            print(door_seal_log_registry)

            fields={str(i.name):{'default':getattr(door_seal_log_registry,i.name),'type':str(i.type).lower()} for i in door_seal_log_registry.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(door_seal_log_registry)
                session.commit()
                return
            for k in fb:
                setattr(door_seal_log_registry,k,fb[k])
            door_seal_log_registry.dtoe=datetime.now()
            session.commit()
            session.refresh(door_seal_log_registry)
            print(door_seal_log_registry)
            return door_seal_log_registry

    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''
        for xnum,i in enumerate(data):
            msg=f"""
{Fore.light_green}{'-'*os.get_terminal_size().columns}{Style.reset}
{Fore.orange_red_1}dsrid={Fore.light_green}"{i.dsrid}"{Style.reset}
{Fore.light_yellow}SealId={Fore.light_green}"{i.SealId}"{Style.reset}
{Fore.light_red}RegisteredBy={Fore.light_green}"{i.RegisteredBy}"{Style.reset}
{Fore.light_blue}dtoe={Fore.light_green}"{i.dtoe}"{Style.reset}
{Fore.light_cyan}comment={Fore.light_green}"{i.comment}"{Style.reset}
{Fore.cyan}photoSerialNo={Fore.light_green}"{i.photoSerialNo}"{Style.reset}
{Fore.light_red}{'*'*os.get_terminal_size().columns}{Style.reset}
            """
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(DoorSealRegistry).filter(DoorSealRegistry.dsrid==item.dsrid).first()
                return self.newLog(door_seal_log_registry=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(DoorSealRegistry).filter(DoorSealRegistry.dsrid==item.dsrid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            filt=abstract_filter(DoorSealRegistry)

            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                print("exited early")
                return
            if filt is not None:
                query=session.query(DoorSealRegistry).filter(filt)
            else:
                query=session.query(DoorSealRegistry)
            
            
            orderedQuery=orderQuery(query,DoorSealRegistry.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()
            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)



    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 1'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 2'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 3'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 4'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            }
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}Door Seal Registry Logger: {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")

#'''
class DoorSealLogLogger(BTemplate):
    def currentSealMatchesLastNewSeal(self):
        with Session(ENGINE) as session:
            log=session.query(DoorSealLog).order_by(DoorSealLog.dtoe.desc()).first()
            if log is None:
                print(f"{Fore.orange_red_1}There are no logs present!{Style.reset}")
                return
            newSeal=session.query(DoorSealRegistry).filter(or_(DoorSealRegistry.SealId.icontains(log.NewSealId),DoorSealRegistry.SealId==log.NewSealId)).first()
            oldSeal=session.query(DoorSealRegistry).filter(or_(DoorSealRegistry.SealId.icontains(log.OldSealId),DoorSealRegistry.SealId==log.OldSealId)).first()
            if newSeal is None:
                log.doorSealMismatch=True
                if '\nNew Seal is not in Registry\n' not in log.doorSealMisMatchComment:
                    log.doorSealMisMatchComment+="\nNew Seal is not in Registry\n"
            if oldSeal is None:
                log.doorSealMismatch=True
                if '\nOld Seal Is Not in Registry\n' not in log.doorSealMisMatchComment:
                    log.doorSealMisMatchComment+="\nOld Seal Is Not in Registry\n"

            fields={
            'Current Door SealId|SealNo':{
                'default':'INVALID',
                'type':'string',
            },
            }
            msg=f"""
{'-'*os.get_terminal_size().columns}
NewSealId={log.NewSealId}
NewSealDate={log.NewSealDate}
NewSealEmployeeIdOrName={log.NewSealEmployeeIdOrName}
OldSealId={log.OldSealId}
OldSealDate={log.OldSealDate}
OldSealEmplyeeIdOrName={log.OldSealEmplyeeIdOrName}
dtoe={log.dtoe}
comment={log.comment}
doorSealMisMatch="{log.doorSealMisMatch}"   
doorSealMisMatchComment="{log.doorSealMisMatchComment}"
doorSealMisMatchPermitted="{log.doorSealMisMatchPermitted}"
doorSealMisMatchPermittedBy="{log.doorSealMisMatchPermittedBy}"
photoSerialNo={log.photoSerialNo}
{'*'*os.get_terminal_size().columns}
            """
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            else:
                current_seal_id=fd['Current Door SealId|SealNo']
                if log.NewSealId != current_seal_id:
                    errMsg=f'''The Current Door Seal does not match the latest log's NewSealId: {log.NewSealId}'''
                    if errMsg not in log.doorSealMisMatchComment:
                        log.doorSealMisMatchComment+=f"\n{errMsg}\n"
                        session.commit()
                        session.refresh(log)
                        print(log)
                else:
                    print(f"{Fore.green_yellow}Verified! {Fore.light_green}Your are GTG ({Fore.orange_red_1}Good-To-Go{Fore.light_green})!{Style.reset}")

    def isSealValid(self):
        with Session(ENGINE) as session:
            logs=session.query(DoorSealLog).all()
            cta=len(logs)
            for num,log in enumerate(logs):
                newSeal=session.query(DoorSealRegistry).filter(DoorSealRegistry.SealId==log.NewSealId).first()
                oldSeal=session.query(DoorSealRegistry).filter(DoorSealRegistry.SealId==log.OldSealId).first()
                #print('seals','old',oldSeal,'new',newSeal,log)
                if not newSeal:
                    log.doorSealMisMatch=True
                    session.commit()
                    session.refresh(log)
                    if log.doorSealMisMatchComment is None:
                        log.doorSealMisMatchComment=''
                        session.commit()
                        session.refresh(log)
                    if '\nNew Seal is not in Registry\n' not in log.doorSealMisMatchComment:
                        log.doorSealMisMatchComment+="\nNew Seal is not in Registry\n"
                if not oldSeal:
                    log.doorSealMisMatch=True
                    session.commit()
                    session.refresh(log)
                    if log.doorSealMisMatchComment is None:
                        log.doorSealMisMatchComment=''
                        session.commit()
                        session.refresh(log)
                    if '\nOld Seal Is Not in Registry\n' not in log.doorSealMisMatchComment:
                        log.doorSealMisMatchComment+="\nOld Seal Is Not in Registry\n"
                
                fields={
                'doorSealMisMatchComment':{
                    'default':'',
                    'type':'string',
                },
                'doorSealMisMatchPermitted':{
                    'default':False,
                    'type':'boolean',
                },
                'doorSealMisMatchPermittedBy':{
                    'default':'string',
                    'type':'',
                },
                'photoSerialNo':{
                    'default':'',
                    'type':'string',
                },

                }
                msg=f"""
{'-'*os.get_terminal_size().columns}
NewSealId={log.NewSealId}
NewSealDate={log.NewSealDate}
NewSealEmployeeIdOrName={log.NewSealEmployeeIdOrName}
OldSealId={log.OldSealId}
OldSealDate={log.OldSealDate}
OldSealEmplyeeIdOrName={log.OldSealEmplyeeIdOrName}
dtoe={log.dtoe}
comment={log.comment}
doorSealMisMatch="{log.doorSealMisMatch}"   
doorSealMisMatchComment="{log.doorSealMisMatchComment}"
doorSealMisMatchPermitted="{log.doorSealMisMatchPermitted}"
doorSealMisMatchPermittedBy="{log.doorSealMisMatchPermittedBy}"
photoSerialNo={log.photoSerialNo}
{'*'*os.get_terminal_size().columns}
                """
                if log.doorSealMisMatch:
                    fd=FormBuilder(data=fields,passThruText=msg)
                    if fd is None:
                        return
                    else:
                        for k in fd:
                            if isinstance(fd[k],str):
                                if fd[k] is not None:
                                    if getattr(log,k) is not None:
                                        if fd[k] not in getattr(log,k):
                                            setattr(log,k,getattr(log,k,)+fd[k])
                                    else:
                                        setattr(log,k,fd[k])

                            else:
                                setattr(log,k,fd[k])

                    session.commit()
                    session.refresh(log)
                    print(log)
    

    def fix_table(self):
        DoorSealLog.__table__.drop(ENGINE)
        DoorSealLog.metadata.create_all(ENGINE)
        print("Done!")



    def newLog(self,door_seal_log=None):
        if door_seal_log:
            arg=True
        else:
            arg=False
        with Session(ENGINE) as session:
            excludes=['dslid',]
            provided=False
            print(door_seal_log)
            if door_seal_log is None:
                door_seal_log=DoorSealLog()
            else:
                provided=True

            if not provided:
                session.add(door_seal_log)
                session.commit()
                session.refresh(door_seal_log)
            else:
                door_seal_log=session.query(DoorSealLog).filter(DoorSealLog.dslid==door_seal_log.dslid).first()
            print(door_seal_log)

            fields={str(i.name):{'default':getattr(door_seal_log,i.name),'type':str(i.type).lower()} for i in door_seal_log.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(door_seal_log)
                session.commit()
                return
            for k in fb:
                setattr(door_seal_log,k,fb[k])
            door_seal_log.dtoe=datetime.now()
            session.commit()
            session.refresh(door_seal_log)
            print(door_seal_log)
            return door_seal_log
    '''
    def newLog(self,doorSealLogObj=None):
        if doorSealLogObj:
            arg=True
        else:
            arg=False

        with Session(ENGINE) as session:
            excludes=['dslid',]
            provided=False
            #print(doorSealLog,"#0")
            if doorSealLogObj is None:
                doorSealLog=DoorSealLog()
            else:
                doorSealLog=doorSealLogObj
                provided=True

            if not provided:
                session.add(doorSealLog)
                session.commit()
                session.refresh(doorSealLog)
            else:
                doorSealLog=session.query(doorSealLog).filter(doorSealLog.dslid==doorSealLogObj.dslid).first()
            #print(doorSealLog,'#1')

            fields={str(i.name):{'default':getattr(doorSealLog,i.name),'type':str(i.type).lower()} for i in doorSealLog.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(doorSealLog)
                session.commit()
                return
            for k in fb:
                setattr(doorSealLog,k,fb[k])
            doorSealLog.dtoe=datetime.now()
            session.commit()
            session.refresh(doorSealLog)
            #print(doorSealLog,'#2')
            return doorSealLog
    '''
    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''
        for xnum,i in enumerate(data):
            msg=f"""
{Fore.light_green}{'-'*os.get_terminal_size().columns}{Style.reset}
{Fore.light_green}NewSealId{Fore.light_yellow}="{i.NewSealId}"{Style.reset}
{Fore.light_green}NewSealDate{Fore.light_yellow}="{i.NewSealDate}"{Style.reset}
{Fore.light_green}NewSealEmployeeIdOrName{Fore.light_yellow}="{i.NewSealEmployeeIdOrName}"{Style.reset}
{Fore.orange_red_1}OldSealId{Fore.dark_goldenrod}="{i.OldSealId}"{Style.reset}
{Fore.orange_red_1}OldSealDate{Fore.dark_goldenrod}="{i.OldSealDate}"{Style.reset}
{Fore.orange_red_1}OldSealEmplyeeIdOrName{Fore.dark_goldenrod}="{i.OldSealEmplyeeIdOrName}"{Style.reset}
{Fore.light_cyan}dtoe{Fore.cyan}="{i.dtoe}{Style.reset}"
{Fore.light_cyan}comment{Fore.cyan}="{i.comment}{Style.reset}"
{Fore.light_red}doorSealMisMatch={Fore.grey_85}"{i.doorSealMisMatch}"   {Style.reset}
{Fore.light_red}doorSealMisMatchComment={Fore.grey_85}"{i.doorSealMisMatchComment}"{Style.reset}
{Fore.light_red}doorSealMisMatchPermitted={Fore.grey_85}"{i.doorSealMisMatchPermitted}"{Style.reset}
{Fore.light_red}doorSealMisMatchPermittedBy={Fore.grey_85}"{i.doorSealMisMatchPermittedBy}"{Style.reset}
{Fore.light_steel_blue}photoSerialNo={Fore.light_red}"{i.photoSerialNo}"{Style.reset}
{Fore.light_red}{'*'*os.get_terminal_size().columns}{Style.reset}
            """
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(DoorSealLog).filter(DoorSealLog.dslid==item.dslid).first()
                return self.newLog(door_seal_log=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(DoorSealLog).filter(DoorSealLog.dslid==item.dslid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            filt=abstract_filter(DoorSealLog)

            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                print("exited early")
                return
            if filt is not None:
                query=session.query(DoorSealLog).filter(filt)
            else:
                query=session.query(DoorSealLog)
            
            
            orderedQuery=orderQuery(query,DoorSealLog.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()
            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)



    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 1'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 2'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 3'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 4'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            },
            str(uuid1()):{
            'cmds':['validate','verify','v/v','vfy','vldt'],
            'exec':self.isSealValid,
            'desc':"Validate Seals"
            },
            str(uuid1()):{
            'cmds':['check seal','chk sl','chksl',],
            'exec':self.currentSealMatchesLastNewSeal,
            'desc':"check to see if current door seal is the last door seal logged."
            },
            
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}Door Seal Log Logger: {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")
def depreciation(): 
    manufacture_date=datetime(2024,11,23)
    expiration_date=datetime(2025,12,5)
    today=datetime.now()
    retail_price=2.99
    getRidOfPrice=0.25
    fields={
    'manufacture_date':{
    'default':manufacture_date,
    'type':'datetime',
    },
    'expiration_date':{
    'default':expiration_date,
    'type':'datetime'
    },
    'today':{
    'default':today,
    'type':'datetime'
    },
    'retail_price':{
    'default':retail_price,
    'type':'float'
    },
    'getRidOfPrice':{
    'default':getRidOfPrice,
    'type':'float'
    },
    }
    fd=FormBuilder(data=fields,passThruText="Product Details")
    if fd is None:
        return
    getRidOfPrice=fd['getRidOfPrice']
    manufacture_date=fd['manufacture_date']
    expiration_date=fd['expiration_date']
    today=fd['today']
    retail_price=fd['retail_price']

    timeLeft=expiration_date-today
    atMostTime=expiration_date-manufacture_date
    
    depreciationValue=1-(timeLeft/atMostTime)
    lostValue=retail_price*depreciationValue
    
    endZone=(timedelta(days=(timeLeft/lostValue).days/getRidOfPrice))
    toPriceAtAQuarter=expiration_date-endZone
    fireSale=retail_price-lostValue
    msg=f'''
{Fore.light_red}Depreciated By{Fore.grey_85}: {depreciationValue}{Style.reset}
{Fore.light_red}Lost Value{Fore.grey_85}: {lostValue}{Style.reset}

{Fore.light_yellow}FireSale{Fore.grey_85}: {fireSale}{Style.reset}
{Fore.light_green}Retail Price{Fore.grey_85}: {retail_price}{Style.reset}
{Fore.orange_red_1}GetRidOfPrice{Fore.grey_85}: {getRidOfPrice}{Style.reset}

{Fore.light_magenta}Expiration/Throw Out Date{Fore.grey_85}: {expiration_date}{Style.reset}
{Fore.light_cyan}Manufacture Or RX Date {Fore.grey_85}: {manufacture_date}{Style.reset}

{Fore.light_yellow}Time Left{Fore.grey_85}: {timeLeft}{Style.reset}
{Fore.light_steel_blue}Total Time{Fore.grey_85}: {atMostTime}{Style.reset}

{Fore.magenta}ToPriceAtAQuarter{Fore.grey_85}: {toPriceAtAQuarter}{Style.reset}
{Fore.cyan}TimeFromQuarterDollarPriceToExpiry{Fore.grey_85}: {endZone}{Style.reset}
    '''
    return msg
    


def TotalToComplete():
    msg='BareMinimumToComplete*DaysToComplete=TotalToComplete'
    while True:
        try:
            fields={
                'Bare Minimum To Complete':{
                'type':'float',
                'default':3.8333,
                },
                'Days To Complete':{
                'type':'float',
                'default':3
                },
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
                
            

            value=fd['Bare Minimum To Complete']*timedelta(days=fd['Days To Complete']).days

            return value
        except Exception as e:
            print(e)


def DaysToComplete():
    msg='TotalToComplete/BareMinimumToComplete=DaysToComplete'
    while True:
        try:
            fields={
                'TotalToComplete':{
                'type':'float',
                'default':11.5,
                },
                'Bare Minimum To Complete':{
                'type':'float',
                'default':3
                },
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
                
            

            value=timedelta(days=fd['TotalToComplete']/fd['Bare Minimum To Complete'])

            return value
        except Exception as e:
            print(e)

def BareMinimumToComplete():
    msg='TotalToComplete/DaysToComplete=BareMinimumToComplete'
    while True:
        try:
            fields={
                'TotalToComplete':{
                'type':'float',
                'default':11.5,
                },
                'Days To Complete':{
                'type':'float',
                'default':3
                },
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
                
            

            value=fd['TotalToComplete']/fd['Days To Complete']

            return value
        except Exception as e:
            print(e)

def CheckInOut():
    msg='CheckIn/Store||CheckOut/Taken'
    while True:
        try:
            fields={
                'Pallet ID':{
                'type':'float',
                'default':11.5,
                },
                'Case ID':{
                'type':'float',
                'default':3
                },
                'stored||taken':{
                'default':'unspecified',
                'type':'string'
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
                
            

            value=f"Pallet Id:{fd['Pallet ID']} CaseId:{fd['Case ID']} stored||taken:{fd['stored||taken']}"

            return value
        except Exception as e:
            print(e)

def SpecificVolume():
    msg='Volume/Mass=SpecificVolume'
    while True:
        try:
            fields={
                'Volume':{
                'type':'string',
                'default':'0.5 oz',
                },
                'Mass':{
                'type':'string',
                'default':'1 gram'
                },
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
                
            

            value=pint.Quantity(fd['Volume'])/pint.Quantity(fd['Mass'])
            print(f"{Fore.orange_red_1}{value}{Style.reset}")
            selector=[
            value,str(value),value.magnitude,value.units
            ]
            htext=[]
            cta=len(selector)
            for num,i in enumerate(selector):
                htext.append(std_colorize(f'{i} - {type(i)}',num,cta))
            htext='\n'.join(htext)
            which=Control(func=FormBuilderMkText,ptext=f"{htext}\nwhich index to use for return",helpText=htext,data="integer")
            if which is None:
                return
            check=[num for num,i in enumerate(selector)]
            if which not in check:
                return selector[-2]
            elif which in ['d',]:
                return selector[-2]
            else:
                return selector[which]

        except Exception as e:
            print(e)

class HeightWeightWaistLogger(BTemplate):
    

    def fix_table(self):
        HeightWeightWaist.__table__.drop(ENGINE)
        HeightWeightWaist.metadata.create_all(ENGINE)
        print("Done!")


    def newLog(self,HeightWeightWaistObj=None):
        if HeightWeightWaist:
            arg=True
        else:
            arg=False

        with Session(ENGINE) as session:
            excludes=['hwwid',]
            provided=False
            #print(HeightWeightWaist,"#0")
            if HeightWeightWaistObj is None:
                HeightWeightWaistObj=HeightWeightWaist()
            else:
                provided=True

            if not provided:
                session.add(HeightWeightWaistObj)
                session.commit()
                session.refresh(HeightWeightWaistObj)
            else:
                HeightWeightWaistObj=session.query(HeightWeightWaist).filter(HeightWeightWaist.hwwid==HeightWeightWaistObj.hwwid).first()
            #print(HeightWeightWaist,'#1')

            fields={str(i.name):{'default':getattr(HeightWeightWaistObj,i.name),'type':str(i.type).lower()} for i in HeightWeightWaistObj.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(HeightWeightWaistObj)
                session.commit()
                return
            for k in fb:
                setattr(HeightWeightWaistObj,k,fb[k])
            HeightWeightWaistObj.dtoe=datetime.now()
            session.commit()
            session.refresh(HeightWeightWaistObj)
            #print(HeightWeightWaist,'#2')
            return HeightWeightWaistObj

    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''
        for xnum,i in enumerate(data):
            height=None
            try:
                height=pint.Quantity(i.Height,i.HeightUnit)
            except Exception as e:
                height=f"{i.Height} {i.HeightUnit}"
                print(e)

            weight=None
            try:
                weight=pint.Quantity(i.Weight,i.WeightUnit)
            except Exception as e:
                weight=f"{i.Weight} {i.WeightUnit}"
                print(e)

            waist=None
            try:
                waist=pint.Quantity(i.Waist,i.WaistUnit)
            except Exception as e:
                waist=f"{i.Waist} {i.WaistUnit}"
                print(e)

            msg=f"""
{Fore.light_green}{'*'*os.get_terminal_size().columns}{Style.reset}
{Fore.orange_red_1}Name:{Fore.medium_violet_red}"{i.Name}"
{Fore.light_green}Height:{Fore.light_cyan}"{height}"
{Fore.light_steel_blue}Weight:{Fore.light_yellow}"{weight}"
{Fore.light_red}Waist:{Fore.dark_goldenrod}"{waist}"
{Fore.orange_red_1}hwwid={Fore.light_green}"{i.hwwid}"
{Fore.cyan}dtoe={Fore.grey_85}"{i.dtoe}"
{Fore.cyan}comment={Fore.grey_85}"{i.comment}"
{Fore.magenta}{'-'*os.get_terminal_size().columns}{Style.reset}

            """
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(HeightWeightWaist).filter(HeightWeightWaist.hwwid==item.hwwid).first()
                return self.newLog(HeightWeightWaistObj=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(HeightWeightWaist).filter(HeightWeightWaist.hwwid==item.hwwid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            filt=abstract_filter(HeightWeightWaist)

            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                print("exited early")
                return
            if filt is not None:
                query=session.query(HeightWeightWaist).filter(filt)
            else:
                query=session.query(HeightWeightWaist)
            
            
            orderedQuery=orderQuery(query,HeightWeightWaist.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()
            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)
    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 1'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 2'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 3'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 4'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            }
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}Height Weight Waist Logger: {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")


class PieceCountLogger(BTemplate):
    

    def fix_table(self):
        PieceCount.__table__.drop(ENGINE)
        PieceCount.metadata.create_all(ENGINE)
        print("Done!")


    def newLog(self,PieceCountObj=None):
        if PieceCount:
            arg=True
        else:
            arg=False

        with Session(ENGINE) as session:
            excludes=['pcid',]
            provided=False
            #print(PieceCount,"#0")
            if PieceCountObj is None:
                PieceCountObj=PieceCount()
            else:
                provided=True

            if not provided:
                session.add(PieceCountObj)
                session.commit()
                session.refresh(PieceCountObj)
            else:
                PieceCountObj=session.query(PieceCount).filter(PieceCount.pcid==PieceCountObj.pcid).first()
            #print(PieceCount,'#1')

            fields={str(i.name):{'default':getattr(PieceCountObj,i.name),'type':str(i.type).lower()} for i in PieceCountObj.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(PieceCountObj)
                session.commit()
                return
            for k in fb:
                setattr(PieceCountObj,k,fb[k])
            PieceCountObj.dtoe=datetime.now()
            session.commit()
            session.refresh(PieceCountObj)
            #print(PieceCount,'#2')
            return PieceCountObj

    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''
        for xnum,i in enumerate(data):
            msg=f"""
{Fore.light_green}{'*'*os.get_terminal_size().columns}{Style.reset}
{Fore.orange_red_1}Carts:{Fore.medium_violet_red}"{i.Carts}"
{Fore.light_green}Uboats:{Fore.light_cyan}"{i.Uboats}"
{Fore.light_steel_blue}Pallets:{Fore.light_yellow}"{i.Pallets}"
{Fore.light_magenta}Pallets:{Fore.light_red}"{i.Pallets}"
{Fore.orange_red_1}pcid={Fore.light_green}"{i.pcid}"
{Fore.cyan}dtoe={Fore.grey_85}"{i.dtoe}"
{Fore.cyan}comment={Fore.grey_85}"{i.comment}"
{Fore.magenta}{'-'*os.get_terminal_size().columns}{Style.reset}

            """
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(PieceCount).filter(PieceCount.pcid==item.pcid).first()
                return self.newLog(PieceCountObj=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(PieceCount).filter(PieceCount.pcid==item.pcid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            filt=abstract_filter(PieceCount)

            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                print("exited early")
                return
            if filt is not None:
                query=session.query(PieceCount).filter(filt)
            else:
                query=session.query(PieceCount)
            
            
            orderedQuery=orderQuery(query,PieceCount.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()
            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)
    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 1'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 2'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 3'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 4'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            }
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}PieceCount Logger: {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")


class LocalWeatherPatternLogger(BTemplate):
    

    def fix_table(self):
        LocalWeatherPattern.__table__.drop(ENGINE)
        LocalWeatherPattern.metadata.create_all(ENGINE)
        print("Done!")


    def newLog(self,LocalWeatherPatternObj=None):
        if LocalWeatherPattern:
            arg=True
        else:
            arg=False

        with Session(ENGINE) as session:
            excludes=['lwpid',]
            provided=False
            #print(LocalWeatherPattern,"#0")
            if LocalWeatherPatternObj is None:
                LocalWeatherPatternObj=LocalWeatherPattern()
            else:
                provided=True

            if not provided:
                session.add(LocalWeatherPatternObj)
                session.commit()
                session.refresh(LocalWeatherPatternObj)
            else:
                LocalWeatherPatternObj=session.query(LocalWeatherPattern).filter(LocalWeatherPattern.lwpid==LocalWeatherPatternObj.lwpid).first()
            #print(LocalWeatherPattern,'#1')

            fields={str(i.name):{'default':getattr(LocalWeatherPatternObj,i.name),'type':str(i.type).lower()} for i in LocalWeatherPatternObj.__table__.columns if i.name not in excludes}
            fb=FormBuilder(data=fields,passThruText="if you see #UNUS, then only state that info if it is needed!")
            if fb in [None,]:
                if not arg:
                    session.delete(LocalWeatherPatternObj)
                session.commit()
                return
            for k in fb:
                setattr(LocalWeatherPatternObj,k,fb[k])
            LocalWeatherPatternObj.dtoe=datetime.now()
            session.commit()
            session.refresh(LocalWeatherPatternObj)
            #print(LocalWeatherPattern,'#2')
            return LocalWeatherPatternObj

    def short_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        ii=''

        def tryComfort(value,unit):
            try:
                dp=pint.Quantity(value,unit)
                if dp <= pint.Quantity(54,"degF"):
                    return "Dry and comfortable (pleasant)"
                if dp >= pint.Quantity(55,"degF") and pint.Quantity <= pint.Quantity(65,"degF"):
                    return "Becoming 'sticky' or muggy"
                if dp > pint.Quantity(65,"degF"):
                    return "Humid, oppressive, and uncomfortable"
            except Exception as e:
                return str(e)

        def tryor(value,unit):
            try:
                return pint.Quantity(value,unit)
            except Exception as e:
                return f"{value} {unit}"

        for xnum,i in enumerate(data):
            fmtd=i.dtoe.strftime(f"""{Fore.light_green}%m/%d/%Y 
        %A(%d) of %B, 
        week[Business] %V of year %Y, 
        week[Sunday First] %U of year %Y, 
        week[Monday First] %W of year %Y) 
        @[12H] {Fore.light_cyan}%I:%M %p
        @[24H] {Fore.medium_violet_red}%H:%M""")

            msg=f"""
{Fore.light_green}{'*'*os.get_terminal_size().columns}{Style.reset}
    {Fore.green}location={Fore.grey_85}"{i.location}"{Style.reset}
    {Fore.green}geolocation={Fore.grey_85}"{i.geolocation}"{Style.reset}
    {Fore.green}elevation={Fore.grey_85}"{tryor(i.elevation,i.elevation_unit)}"{Style.reset}
    {Fore.green}elevation_reference={Fore.grey_85}"{i.elevation_reference}"{Style.reset}
    {Fore.dark_green}lwpid={Fore.grey_85}"{i.lwpid}"{Style.reset}
    {Fore.light_steel_blue}precip={Fore.grey_85}"{tryor(i.precip,i.precip_unit)}"{Style.reset}
    {Fore.orange_red_1}current_temp={Fore.grey_85}"{tryor(i.current_temp,i.current_temp_unit)}"{Style.reset}
    {Fore.orange_red_1}high_temp={Fore.grey_85}"{tryor(i.high_temp,i.high_temp_unit)}"{Style.reset}
    {Fore.light_cyan}low_temp={Fore.grey_85}"{tryor(i.low_temp,i.low_temp_unit)}"{Style.reset}
    {Fore.sky_blue_1}atmo_pressure={Fore.grey_85}"{tryor(i.atmo_pressure,i.atmo_pressure_unit)}"{Style.reset}
    {Fore.magenta}wind_speed={Fore.grey_85}"{tryor(i.wind_speed,i.wind_speed_unit)}"{Style.reset}
    {Fore.magenta}wind_direction={Fore.grey_85}{i.wind_direction}"{Style.reset}
    {Fore.light_yellow}humidity={Fore.grey_85}"{i.humidity}"{Style.reset}
    {Fore.light_yellow}dew_point={Fore.grey_85}"{tryor(i.dew_point,i.dew_point_unit)}"{Style.reset}
    {Fore.light_yellow}General Comfort="{Fore.grey_85}{tryComfort(i.dew_point,i.dew_point_unit)}"{Style.reset}
    {Fore.light_yellow}dawn_dtoe={Fore.grey_85}"{i.dawn_dtoe}"{Style.reset}
    {Fore.light_red}dusk_dtoe={Fore.grey_85}"{i.dusk_dtoe}"{Style.reset}
    {Fore.light_green}sunrise_dtoe={Fore.grey_85}"{i.sunrise_dtoe}"{Style.reset}
    {Fore.red}sunset_dtoe={Fore.grey_85}"{i.sunset_dtoe}"{Style.reset}
    {Fore.dark_goldenrod}UV_Index={Fore.grey_85}"{i.UV_Index}"{Style.reset}
    {Fore.green_yellow}dtoe={Fore.grey_85}"{i.dtoe}"{Style.reset}
    {Fore.cyan}DTOE_PROCESSED="{fmtd}"
    {Fore.tan}comment={Fore.grey_85}"{i.comment}"{Style.reset}
{Fore.magenta}{'-'*os.get_terminal_size().columns}{Style.reset}"""
            if not num:
                m=std_colorize(msg,xnum,ct)
            else:
                m=std_colorize(msg,num,ct)
            xtext.append(m)
            if printToScreen:            
                print(m)
        return '\n'.join(xtext)

    def long_view(self,data:list,printToScreen=True,num=None):
        xtext=[]
        ct=len(data)
        for numx,i in enumerate(data):
            if not num:
                m=std_colorize(i,numx,ct)
            else:
                m=std_colorize(i,num,ct)
            xtext.append(m)
            if printToScreen:
                print(m)
        return '\n'.join(xtext)


    def edit_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(LocalWeatherPattern).filter(LocalWeatherPattern.lwpid==item.lwpid).first()
                return self.newLog(LocalWeatherPatternObj=log)
        except Exception as e:
            print(e)
            return item
        pass

    def delete_id(self,item):
        try:
            with Session(ENGINE) as session:
                log=session.query(LocalWeatherPattern).filter(LocalWeatherPattern.lwpid==item.lwpid).first()
                session.delete(log)
                session.commit()
        except Exception as e:
            print(e)
            return item
        pass

    def search_and_menu(self,menu=False,short=True):
        with Session(ENGINE) as session:
            filt=abstract_filter(LocalWeatherPattern)

            core={
                'limit':{
                'default':None,
                'type':"integer"
                },
                'offset':{
                'default':None,
                'type':'integer,'
                }
            }
            fd=FormBuilder(data=core,passThruText="limit your results.")
            if fd is None:
                print("exited early")
                return
            if filt is not None:
                query=session.query(LocalWeatherPattern).filter(filt)
            else:
                query=session.query(LocalWeatherPattern)
            
            
            orderedQuery=orderQuery(query,LocalWeatherPattern.dtoe)
            limited=limitOffset(orderedQuery,limit=fd['limit'],offset=fd['offset'])
            results=limited.all()
            if short:
                htext=self.short_view(results,False)
            else:
                htext=self.long_view(results,False)

            if menu:
                #next update
                cta=len(results)
                gotoNext=None
                for num,log in enumerate(results):
                    if log == None:
                        continue
                    while True:
                        if log is None:
                            gotoNext=True
                            break
                        
                        cmds=['edit=ed/edit/e','delete=rm/del/delete/remove']
                        try:
                            if short:
                                l=self.short_view([log,],False,num)
                            else:
                                l=self.long_view([log,],False,num)
                            doWhat=Control(func=FormBuilderMkText,ptext=f"{l}\n[{cmds}]?",helpText=f"{l}\n{cmds}",data="string")
                            if doWhat in ['NaN',None]:
                                return
                            elif doWhat.lower() in ['d','']:
                                gotoNext=True
                                break
                            elif doWhat.lower() in [i.lower() for i in 'edit=ed/edit/e'.split('=')[-1].split("/")]:
                                log=self.edit_id(log)

                                continue
                            elif doWhat.lower() in [i.lower() for i in 'delete=rm/del/delete/remove'.split('=')[-1].split("/")]:
                                log=self.delete_id(log)
                                continue
                            else:
                                gotoNext=True
                                break
                            if gotoNext:
                                gotoNext=False
                                break
                        except Exception as e:
                            print(e)
                            gotoNext=True
                            break
            else:
                print(htext)
    def __init__(self):
        cmds={
            str(uuid1()):{
            'cmds':['fixtable','fx tbl'],
            'exec':self.fix_table,
            'desc':"regenerate tables; a complete clear!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 1'],
            'exec':self.search_and_menu,
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 2'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=False),
            'desc':"search and use menu - LONG!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 3'],
            'exec':lambda self=self: self.search_and_menu(short=True),
            'desc':"search and print - Short!!!"
            },
            str(uuid1()):{
            'cmds':['search','sch 4'],
            'exec':lambda self=self: self.search_and_menu(menu=True,short=True),
            'desc':"search and use menu - Short!!!"
            },
            
            str(uuid1()):{
            'cmds':['new log','new','new temp log','ntl'],
            'exec':self.newLog,
            'desc':"create a new log"
            }
        }
        htext=[]
        cta=len(cmds.keys())
        for num,i in enumerate(cmds):
            if str(num) not in cmds[i]['cmds']:
                cmds[i]['cmds'].append(str(num))
            msg=f"{cmds[i]['cmds']} - {Fore.light_green}{cmds[i]['desc']}"
            htext.append(std_colorize(msg,num,cta))
        htext='\n'.join(htext)
        while True:
            doWhat=Control(func=FormBuilderMkText,ptext=f"{Fore.orange_red_1}LocalWeatherPattern Logger: {Fore.light_green}Exec:",helpText=htext,data="string")
            if doWhat in [None,"NaN"]:
                return None
            elif doWhat in ['d','']:
                print(htext)
                continue
            for c in cmds:
                if doWhat.lower() in [i.lower() for i in cmds[c]['cmds']]:
                    if callable(cmds[c]['exec']):
                        try:
                            cmds[c]['exec']()
                        except Exception as e:
                            print(e)
                            break
                    else:
                        print(cmds[c],"!Callable()")


def RandomPrice(base=0,top=75,envelope_max=0.1,decimals=6):
    with localcontext() as ctx:
        ctx.prec=decimals
        rfloat=random.uniform(base,top)
        envelop=random.uniform(rfloat,rfloat+(rfloat*envelope_max))
        return Decimal(rfloat)*1

def RandomCustomerPayment(base=0,top=75,envelope_max=0.1,decimals=6,price=RandomPrice()):
    with localcontext() as ctx:
        ctx.prec=decimals
        if price is None:
            rfloat=random.uniform(base,top)
        else:
            rfloat=float(price)
        envelop=random.uniform(rfloat,rfloat+(rfloat*envelope_max))
        print(f"""Price was: {price}!
Customer Paid: {Decimal(envelop)*1}
Their Change is: {(Decimal(envelop)*1)-(Decimal(rfloat)*1)}
            """)
        return Decimal(envelop)*1

def RandomChange(base=0,top=75,envelope_max=0.1,decimals=6,price=RandomPrice()):
    with localcontext() as ctx:
        ctx.prec=decimals
        if price is None:
            rfloat=random.uniform(base,top)
        else:
            rfloat=float(price)
        envelop=random.uniform(rfloat,rfloat+(rfloat*envelope_max))
        print(f"""Price was: {price}!
Customer Paid: {Decimal(envelop)*1}
Their Change is: {(Decimal(envelop)*1)-(Decimal(rfloat)*1)}
            """)
        return (Decimal(envelop))-(Decimal(rfloat))

