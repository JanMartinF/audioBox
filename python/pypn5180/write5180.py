from .iso_iec_15693 import iso_iec_15693
import time
import binascii
import math

BLOCK_OFFSET = 10 
BLOCK_SIZE = 4 

def write_string_to_tag(stringToWrite):
   full_byte_data = stringToWrite.encode('utf-8')
   num_blocks = math.ceil(len(full_byte_data) / BLOCK_SIZE) 
   blocks_to_write = []
   for i in range(num_blocks):
      start_index = i * BLOCK_SIZE
      end_index = start_index + BLOCK_SIZE
      
      block_data = full_byte_data[start_index:end_index]
      padding_needed = BLOCK_SIZE - len(block_data)
      padded_block_data = block_data + b'\x00' * padding_needed
      
      blocks_to_write.append(list(padded_block_data))
      
      data_hex_string = binascii.hexlify(bytearray(list(padded_block_data))).decode('utf-8')
      print(f"   Block {BLOCK_OFFSET + i}: {data_hex_string}")
   
   #add one empty block as delimiter for later reading
   padded_block_data = b'\x00' * BLOCK_SIZE
   blocks_to_write.append(list(padded_block_data))
   try:
      print("\n[1] Initializing reader...")
      reader = iso_iec_15693()
      print("\n[2] Waiting for ISO 15693 Tag (Attempt 1 of 10)...")
      inventory_frame = [0x26, 0x01, 0x00]
      flags, data = (0xFF, [])
      for i in range(1, 11):
         if i > 1:
               print(f"Waiting for ISO 15693 Tag (Attempt {i} of 10)...")
         
         flags, data = reader.pn5180.transactionIsoIec15693(inventory_frame) 
         
         if len(data) == 9 or (flags == 0x00 and len(data) > 0): 
               break
         time.sleep(0.75) 

      if len(data) != 9 and flags != 0x00:
         print("Error: No ISO 15693 tag detected or responded.")
         return False
         
      dsfid = hex(data[0])
      uid_bytes = data[1:]
      uid_hex = binascii.hexlify(bytearray(uid_bytes)).decode('utf-8')
      
      print(f"Tag Found! UID: {uid_hex}, DSFID: {dsfid}")
      time.sleep(0.1)

      all_writes_successful = True
      
      for i, block_data_list in enumerate(blocks_to_write):
         current_block = BLOCK_OFFSET + i
         for attempt in range(1, 5):
            print(f"\n[3] Writing Block {current_block} ({len(block_data_list)} bytes) (Attempt {attempt})...")
            _, errStr = reader.writeSingleBlockCmd(current_block, block_data_list) 
            if 'OK' in errStr:
               print(f"Success! Block {current_block} written.")
               break
            elif "No Answer from tag" in errStr:
               print("Write Error: No Answer from tag. Retrying...")
               time.sleep(0.2) 
            else:
               print(f"Write Error on Block {current_block}: {errStr}")
               all_writes_successful = False
               break 
               
      return all_writes_successful
            
   except Exception as e:
      print(f"\nAn unhandled error occurred: {e}")