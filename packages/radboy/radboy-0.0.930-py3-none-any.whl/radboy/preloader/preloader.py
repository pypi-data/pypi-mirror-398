from . import *


preloader={
	f'{uuid1()}':{
						'cmds':['volume',],
						'desc':f'find the volume of height*width*length without dimensions',
						'exec':volume
					},
	f'{uuid1()}':{
						'cmds':['depreciation','price out','fire sale'],
						'desc':f'calculate info for firesale',
						'exec':depreciation,
					},
	f'{uuid1()}':{
            'cmds':['glossary','g'],
            'exec':lambda:GlossaryUI(engine=ENGINE),
            'desc':'terms and definitions related to inventory management'
            	},
	f'{uuid1()}':{
						'cmds':['qty str','qts','qty s',],
						'desc':f'generate a qty text for use with Entry.Note',
						'exec':QtyString
					},
	f'{uuid1()}':{
						'cmds':['dsr','door seal registry',],
						'desc':f'log/register door seals for use with door seals',
						'exec':DoorSealRegistryLogger
					},
	f'{uuid1()}':{
						'cmds':['dsl','door seal log',],
						'desc':f'log door seals in use with door secured doors',
						'exec':DoorSealLogLogger
					},
	f'{uuid1()}':{
						'cmds':['bmtc','bare min to cmplt'],
						'desc':f'bare minimum to compete =totalToComplete/DaysToComplete',
						'exec':BareMinimumToComplete
					},
	f'{uuid1()}':{
						'cmds':['hww','height weight waist'],
						'desc':f'track you body\'s size, weight, and height',
						'exec':HeightWeightWaistLogger
					},
	f'{uuid1()}':{
						'cmds':['pcl','piece count logger'],
						'desc':f'track you store load counts',
						'exec':PieceCountLogger
					},
	f'{uuid1()}':{
						'cmds':['rndm prc','random price'],
						'desc':f'generate a random price float within 0 to 75; for tills',
						'exec':RandomPrice
					},
	f'{uuid1()}':{
						'cmds':['rndm chng','random change'],
						'desc':f'generate a random change from price float - customer payment within 0 to 75; for tills',
						'exec':RandomChange
					},
	f'{uuid1()}':{
						'cmds':['chkio','check in out'],
						'desc':f'generate a check in check out string from subsequent data provided by the user',
						'exec':CheckInOut
					},
	'{uuid1()}':{
						'cmds':['sp vlm','secific volume'],
						'desc':f'calculate volume/mass=specificVolume',
						'exec':SpecificVolume
					},
	f'{uuid1()}':{
						'cmds':['lwpl','local weather pattern logger'],
						'desc':f'record local weather data for preview in a later context',
						'exec':LocalWeatherPatternLogger
					},
	f'{uuid1()}':{
						'cmds':['cstmr pay','customer pays what'],
						'desc':f'generate a random payment float that is within 0 to 75+0-10% random extra ; for tills',
						'exec':RandomCustomerPayment
					},
	f'{uuid1()}':{
						'cmds':['dtc','days to cmplt',],
						'desc':f'Days To Complete = totalToComplete/BareMinimumToComplete',
						'exec':DaysToComplete
					},
	f'{uuid1()}':{
						'cmds':['ttc','ttl to cmplt',],
						'desc':f'Total To Complete = BareMinimumToComplete*DaysToComplete',
						'exec':TotalToComplete
					},

	f'{uuid1()}':{
						'cmds':['federal tax withholding',],
						'desc':f'calculate your tax withholding for federal; you will need the IRS Publication 15-T ({datetime.now().year})',
						'exec':FederalIncomeTaxWithholding
					},
	f'{uuid1()}':{
						'cmds':['va state tax withholding',],
						'desc':f'calculate your tax withholding for va state; you will need the "Virginia/VA Employer Withholding Tables" for ({datetime.now().year})',
						'exec':VAStateIncomeTaxWithholding
					},
	f'{uuid1()}':{
						'cmds':['mpgl','mpg log','mpg logger','miles per gallon log'],
						'desc':f'log your miles per gallon, make sure you have a start odometer reading, end odometer reading, and fuel used.',
						'exec':lambda: str(MPGLogger())
					},
	f'{uuid1()}':{
						'cmds':['fpl','fuel price log','fuel log','gas prices','gas'],
						'desc':f'log gas prices for trip planning',
						'exec':lambda: str(GasLogger())
					},
	f'{uuid1()}':{
						'cmds':['value from total mass','vftm'],
						'desc':f'give an estimated total value for mass of currency ((1/unitMass)*ValueOfUnit)*TotalMassOfUnitToBeCounted',
						'exec':TotalCurrencyFromMass
					},
	f'{uuid1()}':{
						'cmds':['base value from mass','bvfm'],
						'desc':f'get base value for each coin to use as the price so qty may be the gram value (1/unitMass)*ValueOfUnit',
						'exec':BaseCurrencyValueFromMass
					},
	f'{uuid1()}':{
						'cmds':['us currency mass','us cnc'],
						'desc':f'get us currency mass values',
						'exec':USCurrencyMassValues
					},
	f'{uuid1()}':{
						'cmds':['drgs','drugs','drug-select','drug select'],
						'desc':f'return a selected drug text',
						'exec':drug_text
					},
	f'{uuid1()}':{
						'cmds':['temp logger','temp log','tmplg'],
						'desc':f'log a temperature',
						'exec':lambda: str(Templogger())
					},
	f'{uuid1()}':{
						'cmds':['mulefraud','mule fraud','mule-fraud','tax fraud mulisha','tax fraud 11.8.2025','consumer fraud 11.8.2025'],
						'desc':f'see what tax fraud values might look like',
						'exec':TaxMuleFraud
					},
	f'{uuid1()}':{
						'cmds':['golden-ratio','gldn rto',],
						'desc':f'get the golden ration for a measurement',
						'exec':golden_ratio
					},
	f'{uuid1()}':{
						'cmds':['volume pint',],
						'desc':f'find the volume of height*width*length using pint to normalize the values',
						'exec':volume_pint
					},
	f'{uuid1()}':{
						'cmds':['cooking units',],
						'desc':f'review conversions for the kitchen',
						'exec':CC_Ui
					},
	f'{uuid1()}':{
						'cmds':['self-inductance pint',],
						'desc':f'find self-inductance using pint to normalize the values for self-inductance=relative_permeability*(((turns**2)*area)/length)*1.26e-6',
						'exec':inductance_pint
					},
	f'{uuid1()}':{
						'cmds':['required resonant LC inductance',],
						'desc':f'find the resonant inductance for LC using L = 1 / (4π²f²C)',
						'exec':resonant_inductance
					},
	f'{uuid1()}':{
						'cmds':['cost to run','c2r'],
						'desc':f'find the cost to run a device per day',
						'exec':costToRun
				    },
	f'{uuid1()}':{
						'cmds':['now to % time','n2pt'],
						'desc':f'now to percent time, or time to go',
						'exec':ndtp
				    },
	f'{uuid1()}':{
						'cmds':['currency conversion','cur-cvt'],
						'desc':f'convert currency from one to the another',
						'exec':currency_conversion,
				    },
	f'{uuid1()}':{
						'cmds':['sonofman-bible','sonofman','bible','bbl'],
						'desc':f'open sonofman bible',
						'exec':bible_try,
				    },
	f'{uuid1()}':{
						'cmds':['sales floor location','sls flr lctn'],
						'desc':f'generate a sales floor location string',
						'exec':SalesFloorLocationString,
				    },
	f'{uuid1()}':{
						'cmds':['backroom location','br lctn'],
						'desc':f'generate a backroom location string',
						'exec':BackroomLocation,
				    },
	f'{uuid1()}':{
						'cmds':['generic item or service text template','txt gios '],
						'desc':f'find the cost to run a device per day',
						'exec':generic_service_or_item
				    },
	f'{uuid1()}':{
						'cmds':['reciept book entry','rbe'],
						'desc':f'reciept book data to name template',
						'exec':reciept_book_entry,
				    },
	f'{uuid1()}':{
						'cmds':['air coil',],
						'desc':f''' 
The formula for inductance - using toilet rolls, PVC pipe etc. can be well approximated by:

                (0.394) * (r**2) * (N**2)
Inductance L = _________________________
              	( 9 * r ) + ( 10 * Len)
Here:
	N = Number of Turns 
	r = radius of the coil i.e. form diameter (in cm.) divided by 2
	Len = length of the coil - again in cm.
	L = inductance in uH.
	* = multiply by
	math.pi**2==0.394
						''',
						'exec':air_coil
					},
					f'{uuid1()}':{
						'cmds':['circumference of a circle using diameter',],
						'desc':f'C=2πr',
						'exec':circumference_diameter
					},
					f'{uuid1()}':{
						'cmds':['circumference of a circle using radius',],
						'desc':f'C=2πr',
						'exec':circumference_radius
					},
					f'{uuid1()}':{
						'cmds':['area of a circle using diameter',],
						'desc':f'A = πr²',
						'exec':area_of_circle_diameter
					},
					f'{uuid1()}':{
						'cmds':['area of a circle using radius',],
						'desc':f'A = πr²',
						'exec':area_of_circle_radius
					},
					f'{uuid1()}':{
						'cmds':['get capacitance for desired frequency with specific inductance',],
						'desc':f'C = 1 / (4π²f²L)²',
						'exec':air_coil_cap,
					},
					f'{uuid1()}':{
						'cmds':['get resonant frequency for lc circuit',],
						'desc':f'f = 1 / (2π√(LC))',
						'exec':lc_frequency,
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['triangle','trngl'],endCmd=['area','a'])],
						'desc':f'A=BH/2 = area of a triangle',
						'exec':area_triangle,
					},
					f'{uuid1()}':{
						'cmds':['taxable kombucha',],
						'desc':f'is kombucha taxable?[taxable=True,non-taxable=False]',
						'exec':lambda: Taxable.kombucha(None),
					},
					f'{uuid1()}':{
						'cmds':['taxable item',],
						'desc':f'is item taxable?[taxable=True,non-taxable=False]',
						'exec':lambda: Taxable.general_taxable(None),
					},
					f'{uuid1()}':{
						'cmds':['price * rate = tax',],
						'desc':f'multiply a price times its tax rate ; {Fore.orange_red_1}Add this value to the price for the {Fore.light_steel_blue}Total{Style.reset}',
						'exec':lambda: price_by_tax(total=False),
					},
					f'{uuid1()}':{
						'cmds':['( price + crv ) * rate = tax',],
						'desc':f'multiply a (price+crv) times its tax rate ; {Fore.orange_red_1}Add this value to the price for the {Fore.light_steel_blue}Total{Style.reset}',
						'exec':lambda: price_plus_crv_by_tax(total=False),
					},
					f'{uuid1()}':{
						'cmds':['(price * rate) + price = total',],
						'desc':f'multiply a price times its tax rate + price return the total',
						'exec':lambda: price_by_tax(total=True),
					},
					f'{uuid1()}':{
						'cmds':['( price + crv ) + (( price + crv ) * rate) = total',],
						'desc':f'multiply a (price+crv) times its tax rate plus (price+crv) and return the total',
						'exec':lambda: price_plus_crv_by_tax(total=True),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['cylinder','clndr'],endCmd=['vol rad','volume radius'])],
						'desc':f'obtain the volume of a cylinder using radius',
						'exec':lambda: volumeCylinderRadius(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['cylinder','clndr'],endCmd=['vol diam','volume diameter'])],
						'desc':f'obtain the volume of a cylinder using diameter',
						'exec':lambda: volumeCylinderDiameter(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['cone',],endCmd=['vol rad','volume radius'])],
						'desc':f'obtain the volume of a cone using radius, a cone is 1/3 of a cylinder at the same height and radius',
						'exec':lambda: volumeConeRadius(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['cone',],endCmd=['vol diam','volume diameter'])],
						'desc':f'obtain the volume of a cone using diameter, a code is 1/3 of a cylinder at the same height and diameter',
						'exec':lambda: volumeConeDiameter(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['hemisphr','hemisphere'],endCmd=['vol rad','volume radius'])],
						'desc':f'obtain the volume of a hemisphere using radius',
						'exec':lambda: volumeHemisphereRadius(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['hemisphr','hemisphere'],endCmd=['vol diam','volume diameter'])],
						'desc':f'obtain the volume of a hemisphere using diameter',
						'exec':lambda: volumeHemisphereDiameter(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['circle',],endCmd=['area radius','area rad'])],
						'desc':f'obtain the area of a circle using radius',
						'exec':lambda: areaCircleRadius(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['circle',],endCmd=['area diameter','area diam'])],
						'desc':f'obtain the area of a circle using diameter',
						'exec':lambda: areaCircleDiameter(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['sudoku',],endCmd=['candidates','cd'])],
						'desc':f'obtain candidates for sudoku cell',
						'exec':lambda: sudokuCandidates(),
					},
					f'{uuid1()}':{
						'cmds':[i for i in generate_cmds(startcmd=['sudoku',],endCmd=['candidates auto','cda'])],
						'desc':f'obtain candidates for sudoku cell for the whole grid',
						'exec':lambda: candidates(),
					},
					f'{uuid1()}':{
						'cmds':['herons formula','hrns fmla'],
						'desc':f'''
Heron's formula calculates the area of any 
triangle given only the lengths of its 
three sides (a, b, and c). The formula is: 
Area = √(s(s-a)(s-b)(s-c)). To use it, first
 calculate the semi-perimeter, s = (a + b 
 + c) / 2, and then substitute this value 
 and the side lengths into the formula to 
 find the area. 
						''',
						'exec':lambda: heronsFormula(),
					},
					f'{uuid1()}':{
						'cmds':['tax add',],
						'desc':'''AddNewTaxRate() -> None

add a new taxrate to db.''',
						'exec':lambda: AddNewTaxRate(),
					},
					f'{uuid1()}':{
						'cmds':['tax get',],
						'desc':	'''GetTaxRate() -> TaxRate:Decimal

search for and return a Decimal/decc
taxrate for use by prompt.
''',
						'exec':lambda: GetTaxRate(),
					},
					f'{uuid1()}':{
						'cmds':['tax delete',],
						'desc':'''DeleteTaxRate() -> None

search for and delete selected
taxrate.
''',
						'exec':lambda: DeleteTaxRate(),
					},
					f'{uuid1()}':{
						'cmds':['tax edit',],
						'desc':'''EditTaxRate() -> None

search for and edit selected
taxrate.
''',
						'exec':lambda: EditTaxRate(),
					},
}
