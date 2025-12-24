import struct
import random
import numpy as np
from PIL import Image
from reedsolo import RSCodec, ReedSolomonError

class GhostTag:
    def __init__(self, redundancy=20, seed=42):
        """
        Initialize the GhostTag steganography engine.
        
        Args:
            redundancy (int): Number of error correction bytes. Higher = more robust, less capacity.
            seed (int): The "password" used to scatter bits. Without this seed, data is invisible noise.
        """
        self.rsc = RSCodec(redundancy)
        self.seed = seed
        # Header is always fixed size: 4 bytes (int) + 4 bytes (ECC) = 8 bytes total
        self.header_rsc = RSCodec(4)

    def _get_indices(self, total_pixels):
        """Generates a reproducible, randomized list of pixel indices."""
        indices = list(range(total_pixels))
        random.seed(self.seed)
        random.shuffle(indices)
        return indices

    def _bits_to_bytes(self, bits):
        """Helper to convert bit array back to bytes."""
        byte_array = bytearray()
        for i in range(0, len(bits), 8):
            byte_chunk = bits[i:i+8]
            if len(byte_chunk) < 8: break
            byte_val = int(''.join(map(str, byte_chunk)), 2)
            byte_array.append(byte_val)
        return bytes(byte_array)

    def _bytes_to_bits(self, data):
        """Helper to convert bytes to bit array."""
        bits = []
        for byte in data:
            bits.extend([(byte >> i) & 1 for i in range(7, -1, -1)])
        return bits

    def embed(self, image_path, message, output_path):
        """
        Embeds a string message into an image file.
        Saves as PNG to preserve integrity (Fragile Mode).
        """
        img = Image.open(image_path).convert('RGB')
        # Flatten image to 1D array of pixels
        pixels = np.array(img).flatten()
        
        # 1. ENCODE PAYLOAD
        msg_bytes = message.encode('utf-8')
        protected_payload = self.rsc.encode(msg_bytes)
        
        # 2. ENCODE HEADER (Length of payload)
        length_val = len(protected_payload)
        length_bytes = struct.pack('>I', length_val) # 4 bytes unsigned int
        protected_header = self.header_rsc.encode(length_bytes)
        
        # 3. COMBINE
        full_data = protected_header + protected_payload
        bits_to_hide = self._bytes_to_bits(full_data)
        
        # 4. CAPACITY CHECK
        if len(bits_to_hide) > len(pixels):
            raise ValueError(f"Capacity exceeded. Need {len(bits_to_hide)} pixels, image has {len(pixels)}.")

        # 5. SCATTER & INJECT
        indices = self._get_indices(len(pixels))
        
        for i, bit_val in enumerate(bits_to_hide):
            idx = indices[i]
            # Clear LSB (mask 0xFE) and set new bit
            pixels[idx] = (pixels[idx] & 0xFE) | bit_val

        # 6. RECONSTRUCT & SAVE
        h, w, c = np.array(img).shape
        result_img = Image.fromarray(pixels.reshape((h, w, c)).astype('uint8'))
        
        if not output_path.lower().endswith(".png"):
            output_path += ".png"
            
        result_img.save(output_path)
        return output_path

    def extract(self, image_path):
        """
        Extracts and attempts to repair the message from an image.
        Returns: Tuple (Success: bool, Message/Error: str)
        """
        try:
            img = Image.open(image_path).convert('RGB')
            pixels = np.array(img).flatten()
            
            # 1. READ HEADER BITS
            indices = self._get_indices(len(pixels))
            
            # Header is fixed 8 bytes (4 data + 4 ECC) = 64 bits
            header_bits = []
            for i in range(64):
                idx = indices[i]
                header_bits.append(pixels[idx] & 1)
                
            # 2. DECODE HEADER
            header_bytes = self._bits_to_bytes(header_bits)
            decoded_header = self.header_rsc.decode(header_bytes)[0]
            payload_length = struct.unpack('>I', decoded_header)[0]
            
            # 3. READ PAYLOAD BITS
            total_bits_needed = 64 + (payload_length * 8)
            
            if total_bits_needed > len(pixels):
                return False, "Header corrupted: Invalid length detected."

            payload_bits = []
            for i in range(64, total_bits_needed):
                idx = indices[i]
                payload_bits.append(pixels[idx] & 1)
                
            payload_bytes = self._bits_to_bytes(payload_bits)
            
            # 4. DECODE PAYLOAD
            decoded_message = self.rsc.decode(payload_bytes)[0]
            return True, decoded_message.decode('utf-8')

        except ReedSolomonError:
            return False, "Data integrity lost. Corruption exceeds repair capacity."
        except Exception as e:
            return False, str(e)