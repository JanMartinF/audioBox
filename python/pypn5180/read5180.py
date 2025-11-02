import binascii

BLOCK_OFFSET = 10
BLOCK_SIZE = 4

def read_full_tag_content(reader):
   hexResponse = 0
   counter = 0
   fullMessage = ""
   while hexResponse != "00000000":
      current_block = BLOCK_OFFSET + counter
      read_data, read_err = reader.readSingleBlockCmd(current_block) 
      if 'OK' in read_err:
         hexResponse = binascii.hexlify(bytearray(read_data)).decode('utf-8')
         if len(read_data) != BLOCK_SIZE:
            print(f"Block {current_block} Read data length mismatch! Expected {BLOCK_SIZE} bytes, got {len(read_data)}")
            break
         read_string_partial = bytes(read_data).decode('utf-8', errors='ignore').strip('\x00')
         fullMessage += read_string_partial
      else:
         print(f"Read Error during verification of Block {current_block}: {read_err}", flush=True)
         break
      counter += 1
   return fullMessage