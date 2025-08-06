# Author: Marco Simoes
# Adapted from Java's implementation of Rui Pedro Paiva
# Teoria da Informacao, LEI, 2022

import sys
from huffmantree import HuffmanTree

#Classe responsável por ler e armazenar os campos do cabeçalho (Header) do ficheiro gzip.
class GZIPHeader:
	#Os campos ID1 e ID2, inicializados com o valor 0, representam um número que identifica o tipo de ficheiro (ID1 = 0x1f, ID2 = 0x8b).
	#O campo CM (Compression Method) representa o método de compressão (Se o ficheiro for comprimido através do método de compressão deflate, então o valor de CM será 8).
	#O campo FLG representa as File Flags.
	#O campo XFL representa as compression flags.
	#O campo OS representa o id do sistema operativo.
	#O campo MTIME representa o 32bit-timestamp de tamanho igual a 4, tal como indica o campo lenMTIME.
	#O campo mTime...
	ID1 = ID2 = CM = FLG = XFL = OS = 0
	MTIME = []
	lenMTIME = 4
	mTime = 0
	# bits 0, 1, 2, 3 and 4, respectively (remaining 3 bits: reserved)
	#O campo FLG (File Flags) disponibiliza Flags extra, sendo estas a que se encontram a baixo (FLG_TEXT, FLG_FHCRC, FLG_FEXTRA, FLG_FNAME, FLG_FCOMMENT).
	#O campo FLG_FTEXT, se definido, os dados não compactados precisam de ser tratados como texto em vez de dados binários.
	#O campo FLG_FHCRC indica que o arquivo contem uma verificação do header através de um algoritmo CRC-32.
	#O campo FLG_FEXTRA indica que o arquivo contem campos extra.
	#O campo FLG_FNAME indica que o arquivo contem o filename original.
	#O campo FLG_FCOMMENT indica que o aquivo contem comentários.
	FLG_FTEXT = FLG_FHCRC = FLG_FEXTRA = FLG_FNAME = FLG_FCOMMENT = 0   
	# FLG_FTEXT --> ignored (usually 0)
	# if FLG_FEXTRA == 1
	XLEN, extraField = [], []
	lenXLEN = 2
	# if FLG_FNAME == 1
	fName = ''  # ends when a byte with value 0 is read
	# if FLG_FCOMMENT == 1
	fComment = ''   # ends when a byte with value 0 is read	
	# if FLG_HCRC == 1
	HCRC = []
		
	#Método responsável por ler e processar o cabeçalho (Header) Huffman do arquivo. Retorna 0 se foi efetuado sem erros ou -1 caso contrário.
	def read(self, f):
		# ID 1 and 2: fixed values
		#São lidos os valores de ID1 e ID2. Tal como mencionado acima, devem ser 0x1f e 0x8b caso sejam do tipo gzip. Caso contrário retorna -1.
		self.ID1 = f.read(1)[0]  
		if self.ID1 != 0x1f: return -1 # error in the header
			
		self.ID2 = f.read(1)[0]
		if self.ID2 != 0x8b: return -1 # error in the header
		
		# CM - Compression Method: must be the value 8 for deflate
		#É lido o campo referente a CM. O valor de CM, tal como mencionado acima, deve ser igual a 8 caso o arquivo tenha sido comprimido através do método de compressão deflate. Caso contrário retorna -1.
		self.CM = f.read(1)[0]
		if self.CM != 0x08: return -1 # error in the header
					
		# Flags
		#É lido o campo referente às flags.
		self.FLG = f.read(1)[0]
		
		# MTIME
		#É lido o campo referente a MTIME (32-bit timestamp).
		self.MTIME = [0]*self.lenMTIME
		self.mTime = 0
		for i in range(self.lenMTIME):
			self.MTIME[i] = f.read(1)[0]
			self.mTime += self.MTIME[i] << (8 * i) 				
						
		# XFL (not processed...)
		#É lido o campo referente a XFL.
		self.XFL = f.read(1)[0]
		
		# OS (not processed...)
		#É lido o campo referente a OS.
		self.OS = f.read(1)[0]
		
		# --- Check Flags
		#São lidas todas as flags extra disponibilizadas pelo campo FLG (File Flags). FLG_FTEXT corresponde ao valor 0x01, FLG_FHCRC ao valor 0x02, FLG_FEXTRA ao valor 0x04, FLG_FNAME ao valor 0x08 e FLG_FCOMMENT ao valor 0x10.
		self.FLG_FTEXT = self.FLG & 0x01
		self.FLG_FHCRC = (self.FLG & 0x02) >> 1
		self.FLG_FEXTRA = (self.FLG & 0x04) >> 2
		self.FLG_FNAME = (self.FLG & 0x08) >> 3
		self.FLG_FCOMMENT = (self.FLG & 0x10) >> 4
					
		# FLG_EXTRA
		#Se o valor de FLG_FEXTRA for igual a 1, significa que o arquivo possui campos extra, pelo que estes são também lidos.
		if self.FLG_FEXTRA == 1:
			# read 2 bytes XLEN + XLEN bytes de extra field
			# 1st byte: LSB, 2nd: MSB
			self.XLEN = [0]*self.lenXLEN
			self.XLEN[0] = f.read(1)[0]
			self.XLEN[1] = f.read(1)[0]
			self.xlen = self.XLEN[1] << 8 + self.XLEN[0]
			
			# read extraField and ignore its values
			self.extraField = f.read(self.xlen)
		
		#Os valores das flags FLG_FNAME, GLG_FCOMMENT e FLG_FHRC correspondem a códigos de 0's e 1's e estes são lidos até surgir o primeiro 0.
		def read_str_until_0(f):
			s = ''
			while True:
				c = f.read(1)[0]
				if c == 0: 
					return s
				s += chr(c)
		
		# FLG_FNAME
		#É lido o valor correspondente à flag FLG_FNAME.
		if self.FLG_FNAME == 1:
			self.fName = read_str_until_0(f)
		
		# FLG_FCOMMENT
		#É lido o valor correspondente à flag FLG_FCOMMENT.
		if self.FLG_FCOMMENT == 1:
			self.fComment = read_str_until_0(f)
		
		# FLG_FHCRC (not processed...)
		#É lido o valor correspondente à flag F_FHCRC.
		if self.FLG_FHCRC == 1:
			self.HCRC = f.read(2)
			
		return 0

#Classe responsável pela deescompressão do ficheiro gzip caso este tenho sido comprimido através do método de compressão deflate.
class GZIP:
	#O campo gzh representa/irá conter o cabeçalho (Header) do ficheiro gzip.
	#O campo gzFile representa/irá conter o nome do ficheiro a descomprimir.
	#O campo fileSize representa/irá conter o tamanho do ficheiro comprimido.
	#O campo origFileSize representa/irá conter o tamanho do ficheiro original, antes da compressão.
	#O campo numBlocks representa/irá conter o número de blocos
	#O campo f representa o "ficheiro".
	gzh = None
	gzFile = ''
	fileSize = origFileSize = -1
	numBlocks = 0
	f = None
	
	bits_buffer = 0
	available_bits = 0		

	#contrutor responsável pela inicialização da classe que recebe como parâmetro o nome do ficheiro a descomprimir (filename).
	#O campo gzFile é responável por guardar o nome do ficheiro.
	#O campo f é responsável por abrir o ficheiro (Em binário).
	#O campo f.seek(0, 2) coloca o "cursor" no inicio do ficheiro até ao ponto de referência 2, que corresponde ao fim do ficheiro, de forma a que o seu tamanho seja obtido no campo seguinte.
	#O campo fileSize é responsável por obter o tamanho do ficheiro ataravés da funcão tell.
	#O campo f.seek(0) coloca o "cursor" no inicio do ficheiro.
	def __init__(self, filename):
		self.gzFile = filename
		self.f = open(filename, 'rb')
		self.f.seek(0,2)
		self.fileSize = self.f.tell()
		self.f.seek(0)

	#Método principal responsável pela descompressão do ficheiro gzip através de um algoritmo deflate.
	def decompress(self):
		#A variável numBlocks representa o número de blocos lidos, inicializado a 0.
		numBlocks = 0

		# get original file size: size of file before compression
		#A variável origFileSize representa o tamanho do ficheiro antes da compressão, obtio pelo método getOrigFileSize() da classe GZIP. Este valor é impresso seguidamente.
		origFileSize = self.getOrigFileSize()
		print(origFileSize)
		
		# read GZIP header
		#É lido o cabeçalho (Header) do ficheiro gzip. A variável error irá conter o valor 0 caso a leitura seja efetuada com sucesso. Caso contrário é impressa uma mensagem de erro e o programa é encerrado. 
		error = self.getHeader()
		if error != 0:
			print('Formato invalido!')
			return
		
		# show filename read from GZIP header
		#É imprimido o nome do ficheiro lido do cabeçalho (Header) do ficheiro gzip.
		print(self.gzh.fName)
		
		# MAIN LOOP - decode block by block
		#Loop principal, responsável pela descodificação bloco por bloco. O loop ocorre enquanto que o valor do bloco BFINAL é diferente de 1.
		BFINAL = 0	
		while not BFINAL == 1:

			#É lido o bit do BFINAL através do método readBits da classe GZIP.
			BFINAL = self.readBits(1)   #É lido 1 bit do buffer (bits_buffer).
							
			#Se o valor de BTYPE for igual a 2 (10 em binário) indica que o bloco foi comprimido com Huffman Dinâmico. Caso contrário é impressa uma mensagem de erro e o programa é encerrado.
			BTYPE = self.readBits(2)   #São lidos 2 bits do buffer (bits_buffer).				
			if BTYPE != 2:
				print('Error: Block %d not coded with Huffman Dynamic coding' % (numBlocks+1))
				return
					
			#--- STUDENTS --- ADD CODE HERE
			# 
			#

			#-------------------------Exercício 1-------------------------

			HLIT = 0
			HDIST = 0
			HCLEN = 0

			HLIT, HDIST, HCLEN = self.readBlockFormat()

			print("\nValue of HLIT: " + str(HLIT))
			print("Value of HDIST: " + str(HDIST))
			print("Value of HCLEN: " + str(HCLEN) + "\n")

			#-------------------------Exercício 2-------------------------

			codeLengths = []

			codeLengthsOrder = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]   #Array que contem as ordens das sequências de 3 bits.

			codeLengths = self.codeLengthsValue(HCLEN, codeLengthsOrder)

			print(str(codeLengths) + "\n")

			#-------------------------Exercício 3-------------------------

			huffmanCodes = {}

			huffmanCodes = self.codeLengthsHuffman(codeLengths)

			print(str(huffmanCodes) + "\n")

			hft = self.generateTree(huffmanCodes)   #Árvore de Huffman com os códigos de Huffman do alfabeto de comprimentos de códigos.

			print("\n")

			#-------------------------Exercício 4-------------------------

			literalLengthsHLIT = []

			literalLengthsHLIT = self.literalLengthValues(hft, HLIT)

			print(str(literalLengthsHLIT) + "\n")

			#-------------------------Exercício 5-------------------------

			literalLengthsHDIST = []

			literalLengthsHDIST = self.literalLengthValues(hft, HDIST)

			print(str(literalLengthsHDIST) + "\n")

			#-------------------------Exercício 6-------------------------

			huffmanCodesHLIT = {}
			huffmanCodesHLITArray = []

			huffmanCodesHLIT = self.codeLengthsHuffman(literalLengthsHLIT)

			print(str(huffmanCodesHLIT) + "\n")

			huffmanCodesHLITArray = self.convertToArray(huffmanCodesHLIT)   #Guarda num array os códigos de Huffman HLIT.

			print(str(huffmanCodesHLITArray) + "\n")

			huffmanCodesHDIST = {}
			huffmanCodesHDISTArray = []

			huffmanCodesHDIST = self.codeLengthsHuffman(literalLengthsHDIST)

			print(str(huffmanCodesHDIST) + "\n")

			huffmanCodesHDISTArray = self.convertToArray(huffmanCodesHDIST)   #Guarda num array os códigos de Huffman HDIST	.

			print(str(huffmanCodesHDISTArray) + "\n")

			hftHLIT = self.generateTree(huffmanCodesHLIT)   #Árvore de Huffman com os códigos de Huffman do alfabeto de literais/comprimentos.

			print("\n")

			hftHDIST = self.generateTree(huffmanCodesHDIST)   #Árvore de Huffman com os códigos de Huffman do alfabeto de distâncias.

			print("\n")
			
			#-------------------------Exercício 7-------------------------

			decompressedOutput = []   #Array que irá conter todos os códigos ASCII.

			decompressedOutput = self.decompressData(hftHLIT, hftHDIST)

			print("\n" + str(decompressedOutput))

			#-------------------------Exercício 8-------------------------

			self.writeFile(decompressedOutput)   #Cria e escreve o conteúdo original num ficheiro de texto com o nome original.

			# update number of blocks read
			#É incrementado em 1 valor o número de blocos lidos.
			numBlocks += 1

		# close file			
		
		self.f.close()	
		print("End: %d block(s) analyzed." % numBlocks)
	
	#Método responsável por ler o formato do bloco, de acordo com a estrutura de cada um (Slide 40 DOC1 / Slide 12 DOC2).
	def readBlockFormat(self):
		#HLIT -> 257 - 286
		HLITValue = self.readBits(5)
		HLITValue = HLITValue + 257

		#HDIST -> 1 - 32
		HDISTValue = self.readBits(5)
		HDISTValue = HDISTValue + 1

		#HCLEN -> 4 - 19
		HCLENValue = self.readBits(4)
		HCLENValue = HCLENValue

		return HLITValue, HDISTValue, HCLENValue

	#Método responsável por armazenar num array os comprimentos dos códigos do "alfabeto de comprimentos de códigos" com base em HCLEN.
	def codeLengthsValue(self, HCLEN, codeLengthsOrder):
		codeLengthsArray = [0] * 19   #Inicializa um array de 0's com tamanho 19.
		HCLENValue = 0

		for i in range(HCLEN + 4):
			HCLENValue = self.readBits(3)
			codeLengthsArray[codeLengthsOrder[i]] = HCLENValue
		
		return codeLengthsArray

	#Método responsável por converter os comprimentos dos códigos do exercício anterior em códigos de Hufman através dos comprimentos dos códigos.
	def codeLengthsHuffman(self, codeLengthsArray):
		huffmanCodesDic = {}   #Dicionário que será retornado com os códigos de Huffman.

		blCountDic = {}
		for i in codeLengthsArray:
			if (i not in blCountDic.keys()):   #Se o valor de comprimento não se encontrar nas keys, este é adicionado e iniciada a sua contagem.
				blCountDic.setdefault(i, 1)

			else:
				blCountDic[i] += 1

		blCountDic = dict(sorted(blCountDic.items()))   #Ordena o dicionário pelas keys (Valores dos comprimentos)

		blCountKeys = []
		for i in blCountDic.keys():   #Guarda no array blCountKeys as keys do dicionário blCountDic de maneira a que seja possível determinar a maior key do dicionário (Que será o tamanho de um array).
			blCountKeys.append(i)

		maxKeyValue = 0
		maxKeyValue = blCountKeys[len(blCountKeys) - 1]
		
		blCountAux = [0] * (maxKeyValue + 1)
		for i in blCountDic.keys():
			blCountAux[i] = blCountDic[i]

		nextCode = [0] * (maxKeyValue + 1)   #Inicializa um array de zeros com tamanho igual ao valor da maior key do dicionário de comprimentos (blCountAux).

		code = 0
		blCountAux[0] = 0
		for i in range(1, len(nextCode)):
			code = (code + blCountAux[i - 1]) << 1   #Deslocamento de bits à esquerda.
			nextCode[i] = code

		huffmanCodesInt = []
		for i in range(len(codeLengthsArray)):
			lenCode = codeLengthsArray[i]

			if (lenCode != 0):
				huffmanCodesInt.append(nextCode[lenCode])
				nextCode[lenCode] += 1

		codeLengthsAux = [i for i in codeLengthsArray if i != 0]   #Array que contém os tamanhos de todos os códigos (Com os zeros removidos).

		huffmanCodes = []
		for i in huffmanCodesInt:
			huffmanCodes.append(format(i, "#010b"))   #Converte o valor diretamente de inteiro para binário adicionando os zeros à esquerda.
			
		for i in range(len(huffmanCodes)):
			huffmanCodes[i] = huffmanCodes[i][2 : len(huffmanCodes[i])]   #Remove os "0b" à frente do número em binário.

		for i in range(len(codeLengthsAux)):
			if (codeLengthsAux[i] < 8):
				zeroPosition = 8 - codeLengthsAux[i]   #São removidos os 0's em excesso à esquerda (Tal ocorre somente nos códigos de comprimento inferior a 8).
				huffmanCodes[i] = huffmanCodes[i][zeroPosition : len(huffmanCodes[i])]

		codeSymbols = [i for i in range(len(codeLengthsArray)) if codeLengthsArray[i] != 0]   #Remove os símbolos cujo valor do comprimento seja igual a 0.
		for i in range(len(codeSymbols)):
			huffmanCodesDic.setdefault(codeSymbols[i], huffmanCodes[i])

		return huffmanCodesDic

	#Método responsável por gerar a árvore de Huffman e adicionar os códigos dos comprimentos de códigos.
	def generateTree(self, huffmanCodes):
		hft = HuffmanTree()   #Inicializa uma árvore de Huffman.
		verbose = True   #Campo verbose que disponibiliza uma mensagem após a inserção na árvore.

		for i in huffmanCodes.keys():
			hft.addNode(huffmanCodes[i], i, verbose)   #huffmanCodes[i] -> código de Huffman, i -> índice do código no alfabeto, verbose -> True ou False.

		return hft

	#Método responsável por ler e armazenar num array os HLIT + 257 ou os HDIST + 1 comprimentos dos códigos referentes ao alfabeto de literais/comprimentos.
	def literalLengthValues(self, hft, HType):
		count = 0
		array = [0] * HType   #É inicializado um array de 0's com tamanho igual a HType (HLIT ou HDIST).

		while (count < HType):   #O código é executado enquanto que o valor do contador for inferior ao valor de HType passado como parâmetro.
			bit = self.readBits(1)
			pos = hft.nextNode(str(bit))
				
			if(pos >= 0):   #Se o valor da variável pos, retornado pelo método nextNode do ficheiro huffmantree.py, for superior a 0, indica que foi encontrada um folha, contendo o valor do seu índice no alfabeto (Corresponde ao símbolo).
				if(pos == 16):   #Se o valor de pos for igual a 16, é necessário repetir o comprimento anterior pelo menos 3 vezes de acordo com os dois próximos bits a ler.
					repeat = 3
					bit = 0

					for i in range(2):
						bits = self.readBits(1)   #É lido um bit do buffer.
						bits = bits << i   #Deslocamento de i bits para a esquerda.
						bit = bit | bits   

					repeat += bit   #A variável repeat contém no número de repetições do comprimento anterior no array de comprimentos de códigos.

					for i in range(repeat):   #É repetido o comprimento anterior n vezes (Pelo menos 3).
						array[count] = array[count-1]   #O valor do comprimento do código de Huffman será igual ao valor do comprimento anterior.
						count += 1   #É incrementado o contador.

				elif(pos == 17):   #Se o valor da variável pos for igual a 17 os próximos códigos terão comprimento igual 0 de acordo com o número de bits extra a ler (Pelo menos 3).
					repeat = 3
					bit = 0

					for i in range(3):
						bits = self.readBits(1)   #É lido um bit do buffer.
						bits = bits << i   #São deslocados i bits para a esquerda.
						bit = bit | bits

					repeat += bit   #A variável repeat contém o número de repetições do comprimento do código de Huffman no array de comprimentos.

					for i in range(repeat):   #Ciclo que irá adicionar o valor do comprimento igual a 0 aos próximos códigos.
						array[count] = 0   #O valor do comprimento do código será 0.
						count += 1   #É incrementado o contador.

				elif(pos == 18):   #Se o valor da variável pos for igual a 18, pelo menos os próximos 11 comprimentos de códigos (11 - 128) serão iguais a 0.
					repeat = 11
					bit = 0

					for i in range(7):
						bits = self.readBits(1)   #É lido um bit do buffer.
						bits = bits << i   #São deslocados i bits para a esquerda.
						bit = bit | bits

					repeat += bit

					for i in range(repeat):   #Ciclo que irá adicionar o valor do comprimento igual 0 aos próximos códigos.
						array[count] = 0   #O valor do comprimento do código será 0.
						count += 1   #É incrementado o contador.

				else:   #Caso contrário, se o valor da variável pos for inferior a 15, este será o valor do comprimento de códigos.
					array[count] = pos
					count += 1

				hft.resetCurNode()   #A posição na Árvore é "reiniciada", isto é volta para a posição inicial, para a raiz.

		return array

	#Método responsável por retornar um array com os códigos de Huffman.
	def convertToArray(self, huffmanCodesHType):
		huffmanCodesArray = []

		for i in huffmanCodesHType.values():
			huffmanCodesArray.append(i)

		return huffmanCodesArray

	#Método responsável pela descompactação dos dados comprimidos com base nos códigos de Huffman e no algoritmo LZ77 (Determina os códigos ASCII para cada caracter).
	def decompressData(self, hftHLIT, hftHDIST):
		outputAscii = []   #Array que será retornado com os valores ASCII de cada caracter.
		pos = 0

		while (pos != 256):   #Enquanto que o valor de pos é diferente de 256 (Quando pos == 256 indica que o bloco foi terminado) são lidos bits e é percorrida a árvore de Huffman do alfabeto de literais/comprimentos.
			bit = self.readBits(1)
			pos = hftHLIT.nextNode(str(bit))   #É percorrida a árvore, se o valor de pos for superior a 0, indica que foi encontrada um folha contendo o seu índice no alfabeto (Corresponde ao símbolo).

			if (pos >= 0):
				if (pos < 256):   #Se o valor de pos for inferior a 256 (Códigos de literais), o valor é adicionado ao array de valores ASCII.
					outputAscii.append(pos)

				else:   #Caso contrário, é ncessário ler bits extra (Códigos de comprimento).
					size = [0, 0]

					if (255 < pos < 265):   #Se o valor de pos estiver entre 255 e 265 o valor do comprimento irá derivar entre 3 a 10 (pos nunca terá o valor 256).
						size[0] = pos - 254

					elif (pos == 285):   #O valor do comprimento para pos == 285 é 258.
						size[0] = 258

					else:   #Caso contrário, se o valor de pos estiver entre 265 e 284 (264 < pos < 285), então será necessário ler bits extra, uma vez que o comprimento poderá variar para esses valores de pos.
						bitsToRead = ((pos - 265) // 4) + 1   #Número de bits a ler.
						aux = 11   #Valor mínimo de comprimento.

						for i in range(1, bitsToRead):
							aux += (4 * (2 ** i))   #Incrementa o valor a somar ao length mínimo conforme o valor em bitsToRead (Bits a ler).

						aux += self.readBits(bitsToRead)   #Valor do comprimento para o símbolo na variável pos.
						
						size[0] = aux

					distCode = -2
					while (distCode < 0):
						distCode = hftHDIST.nextNode(str(self.readBits(1)))   #A árvore hftHDIST é percorrida enquanto que dist < 0.

					hftHDIST.resetCurNode()   #Neste ponto o valor de dist será igual a 0.
					if (distCode < 4):   #Se dist < 4, os códigos terão como valor de Dist 1, 2, 3, 4.
						size[1] = distCode + 1

					else:   #Caso contrário, os valores de Dist variam.
						bitsToRead= ((distCode - 4) // 2) + 1
						aux = 5 

						for i in range (1, bitsToRead):
							aux += (2 * (2 ** i))

						aux += ((distCode - 4) % 2) * (2 ** bitsToRead) + self.readBits(bitsToRead)

						size[1] = aux

					start = len(outputAscii) - size[1]
					for i in range(size[0]):
						outputAscii += [outputAscii[start + i]]
	
				hftHLIT.resetCurNode()

		return outputAscii

	#Método responsável por gravar os dados descompactados num ficheiro com o nome original.
	def writeFile(self, decompressedData):
		fileName = self.gzh.fName   #Nome original do ficheiro previamente guardado na estrutura GZIPHeader, nomeadamente no campo fName.

		f = open(fileName, "w")   #Cria um ficheiro com o nome fileName em write mode.

		dataString = ""   #É inicializa a string dataString que irá conter todo o conteúdo a escrever no ficheiro.
		for i in decompressedData:
			dataString = dataString + chr(i)
		
		f.write(dataString)   #É escrito o conteúdo da string dataString no ficheiro.

		f.close()

		return
	
	#Método responsável por ler o tamanho original do ficheiro antes da compressão.
	def getOrigFileSize(self):
		# saves current position of file pointer
		#A variável fp representa a posição atual do "cursor".
		fp = self.f.tell()
		
		# jumps to end-4 position
		#O "cursor" salta para a posição fileSize - 4.
		self.f.seek(self.fileSize-4)
		
		# reads the last 4 bytes (LITTLE ENDIAN)
		#São lidos os útltimos 4 bytes do ficheiro, em little endian.
		sz = 0
		for i in range(4): 
			sz += self.f.read(1)[0] << (8*i)
		
		# restores file pointer to its original position
		#O "cursor" volta para a posição inicial.
		self.f.seek(fp)
		
		#São retornados a soma dos valores dos últimos 4 bytes, correspondentes ao tamanho do ficheiro.
		return sz		
	
	#Método responsável pela leitura do cabeçalho (Header) do ficheiro gzip.
	#Se a leitura do cabeçalho (Header) for efetuada com sucesso, é retornado o valor 0 pelo método read da classe GZIPHeader, na variável header_error.
	def getHeader(self):
		self.gzh = GZIPHeader()
		header_error = self.gzh.read(self.f)
		return header_error
	
	#Método responsável pela leitura de n bits do bits_buffer Se o valor de keep for True, os bits são deixados no buffer para futuros acessos.
	def readBits(self, n, keep=False):

		#Loop que lê os bits do ficheiro enquanto que há bits disponíveis (available_bits).
		while n > self.available_bits:
			self.bits_buffer = self.f.read(1)[0] << self.available_bits | self.bits_buffer
			self.available_bits += 8   #O valor 8 corresponde ao número de bits num byte.
		
		mask = (2**n)-1
		value = self.bits_buffer & mask

		if not keep:
			self.bits_buffer >>= n
			self.available_bits -= n

		return value

if __name__ == '__main__':

	# gets filename from command line if provided
	fileName = "FAQ.txt.gz"
	if len(sys.argv) > 1:
		fileName = sys.argv[1]			

	# decompress file
	#É inicializada a classe GZIP recebendo o nome do ficheiro como parâmetro, tal como indicado no construtor.
	#É feita a descompressão do ficheiro com recurso ao método decompress da classe GZIP.
	gz = GZIP(fileName)
	gz.decompress()
	