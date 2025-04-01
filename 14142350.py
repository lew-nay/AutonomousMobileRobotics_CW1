#Q1 Answer: 544 complete data frames
#Q2 Answer: 13 corrupt data frames
#Q3 Answer: date: 2016-11-28 UTC 

#import datetime
import csv
import struct

#Open the binary input file
input_file = open("./binaryFileC_65.bin", 'rb')

# array to hold decoded frames for outputting to .csv
decoded_file = []

#Read the first byte and loop as long as
#there is always another byte available
byte = input_file.read(1)

# constants
FRAME_LENGTH: int = 26
FRAME_START = b"%%"

# temperature lookup table
temperature_lookup_table = {
    0xA0: 30.0, 0xA1: 30.1, 0xA2: 30.2, 0xA3: 30.3, 0xA4: 30.4, 0xA5: 30.5, 0xA6: 30.6, 0xA7: 30.7,
    0xA8: 30.8, 0xA9: 30.9, 0xAA: 31.0, 0xAB: 31.1, 0xAC: 31.2, 0xAD: 31.3, 0xAE: 31.4, 0xAF: 31.5,
    0xB0: 31.6, 0xB1: 31.7, 0xB2: 31.8, 0xB3: 31.9, 0xB4: 32.0, 0xB5: 32.1, 0xB6: 32.2, 0xB7: 32.3,
    0xB8: 32.4, 0xB9: 32.5, 0xBA: 32.6, 0xBB: 32.7, 0xBC: 32.8, 0xBD: 32.9, 0xBE: 33.0, 0xBF: 33.1,
    0xC0: 33.2, 0xC1: 33.3, 0xC2: 33.4, 0xC3: 33.5, 0xC4: 33.6, 0xC5: 33.7, 0xC6: 33.8, 0xC7: 33.9,
    0xC8: 34.0, 0xC9: 34.1, 0xCA: 34.2, 0xCB: 34.3, 0xCC: 34.4, 0xCD: 34.5, 0xCE: 34.6, 0xCF: 34.7,
    0xD0: 34.8, 0xD1: 34.9, 0xD2: 35.0, 0xD3: 35.1, 0xD4: 35.2, 0xD5: 35.3, 0xD6: 35.4, 0xD7: 35.5,
    0xD8: 35.6, 0xD9: 35.7, 0xDA: 35.8, 0xDB: 35.9, 0xDC: 36.0, 0xDD: 36.1, 0xDE: 36.2, 0xDF: 36.3
}

# counters
no_correct_frames: int = 0
no_corrupt_frames: int = 0
no_complete_frames: int = 0
no_incomplete_frames: int = 0

def read_frame(frame):
    """Reads in a frame and returns decoded bytes as dictionary"""
    return {
        "sys_id": frame[2],
        "dest_id": frame[3],
        "comp_id": frame[4],
        "seq": frame[5],
        "type": frame[6],
        "ptx": frame[7],
        "rpm_msb": frame[8],
        "rpm_lsb": frame[9],
        "vlt_msb": frame[10],
        "vlt_lsb": frame[11],
        "crt_lsb": frame[12],
        "crt_msb": frame[13],
        "mos_tmp": frame[14],
        "cap_tmp": frame[15],
        "ttx": frame[16],
        "timestamp": int.from_bytes(frame[17:25], byteorder="big"), # combines bytes 18-25 into an integer value with byte 18 being the most significant 
        "checksum": frame[25]
    }

def decode_frame(frame):
    """Reads in a frame as a dictionary, returns human readable frame as array"""
    
    # convert to 16-bit unsigned int
    rpm = (int(frame["rpm_msb"]) << 8) | int(frame["rpm_lsb"]) # bitwise operation, shfts msb by 8 bits, then combines with lsb
    voltage = int((frame["vlt_msb"]) << 8) | int(frame["vlt_lsb"])# same as above

    # convert to 16-bit signed int
    current = struct.unpack("h", bytes([int(frame["crt_lsb"]), int(frame["crt_msb"])]))[0]

    # find temperatures from lookup table
    mosfet_temp = temperature_lookup_table.get(frame["mos_tmp"], 0.0) 
    capacacitor_temp = temperature_lookup_table.get(frame["cap_tmp"], 0.0)

    # convert timestamp from micros to UTC
    #date = datetime.datetime.fromtimestamp(frame["timestamp"] / 1_000_000, datetime.timezone.utc).date()
    #date = datetime.datetime.fromtimestamp(frame["timestamp"] / 1_000_000, datetime.UTC).date()
    #print(date)

    return[
            "~~", 
            frame["sys_id"],
            frame["dest_id"],
            frame["comp_id"],
            frame["seq"],
            frame["type"],
            "P",
            rpm,
            voltage,
            current,
            mosfet_temp,
            capacacitor_temp,
            "T",
            frame["timestamp"],
            frame["checksum"]
        ]


def check_checksum(frame, checksum) -> bool:
    """Checks the checksum of the frame against a calculated
       checksum from the passed frame   
    """
    sum: int = 0

    for i in range(2, 25):
        sum += frame[i]

    remainder = sum % 256

    calculated_check_sum = 255 - remainder

    return checksum == calculated_check_sum


# buffer used to append bytes to until the start of a frame is found
# using byte literal to extact the string
buffer = b''

while byte:
    #print("Byte value is (hexidecimal): " + str(byte))
    #print("Byte value is (decimal): " + str(int.from_bytes(byte)))

    buffer += byte

    if buffer.endswith(FRAME_START): # start of the frame has been found
        #print("buffer == FRAME_START")
        
        # get the full frame
        frame = buffer[-2:] + input_file.read(FRAME_LENGTH - 2) # -2 required as the start frame header is included from the buffer

        if len(frame) == FRAME_LENGTH:
            #print("len(frame) == FRAME_LENGTH")
            no_complete_frames += 1 # is a full-length frame
            #print(frame)
            read_in_frame = read_frame(frame)

            if check_checksum(frame, read_in_frame['checksum']):
                no_correct_frames += 1 # checksum == true so is a valid frame
                #print(frame)

                # is a valid frame so decode the frame and append to the decoded_file array
                decoded_frame = decode_frame(read_in_frame)
                decoded_file.append(decoded_frame)
            else:
                no_corrupt_frames += 1 # checksum == false so corrupt frame

            buffer = b'' # clear vuffer since it was a complete frame
    
        else:
            # incomplete frame
            no_incomplete_frames += 1

            buffer = frame # keep buffer if incomplete frame

    #Get the next byte from the file and repeat    
    byte = input_file.read(1)

# write to .csv file
csv_file="14142350.csv"
with open(csv_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(decoded_file)


#Must be end of the file so close the file
print("End of file reached")
print("Number of frames: " + str(no_complete_frames))
print("Number of correct frames: " + str(no_correct_frames))
print("Number of corrupt frames: " + str(no_corrupt_frames))
print("Number of incomplete frames: " + str(no_incomplete_frames))

input_file.close()
