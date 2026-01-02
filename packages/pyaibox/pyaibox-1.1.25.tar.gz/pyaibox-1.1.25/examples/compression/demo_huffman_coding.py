import os
import pyaibox as pb

path = 'data/files/english_sentence.txt'

# Example usage and demonstration
print("Huffman Compression and Decompression Demo")
print("=" * 50)

# Text compression example
print("\n1. Text Compression Example:")
text_compressor = pb.TextHuffmanCompressor()

sample_text = "This is a sample text for Huffman compression. " * 5
print(f"Original text length: {len(sample_text)} characters")

# Compress text
compressed_data = text_compressor.compress_text(sample_text)
print(f"Compressed size: {len(compressed_data)} bytes")

# Decompress text
decompressed_text = text_compressor.decompress_text(compressed_data)
print(f"Decompression successful: {sample_text == decompressed_text}")

# Calculate compression ratio
original_size = len(sample_text.encode('utf-8'))
ratio = pb.calculate_compression_ratio(original_size, len(compressed_data))
print(f"Compression ratio: {ratio:.2f}%")

# File compression example
print("\n2. File Compression Example:")
file_compressor = pb.FileHuffmanCompressor()

# Create a sample file
sample_content = "This is a test file for Huffman compression.\n" * 100
with open('sample.txt', 'w') as f:
    f.write(sample_content)

# Compress file
success, message = file_compressor.compress_file('sample.txt', 'sample_compressed.bin')
print(f"File compression: {message}")

if success:
    original_size = pb.get_file_size('sample.txt')
    compressed_size = pb.get_file_size('sample_compressed.bin')
    ratio = pb.calculate_compression_ratio(original_size, compressed_size)
    
    print(f"Original file size: {original_size} bytes")
    print(f"Compressed file size: {compressed_size} bytes")
    print(f"File compression ratio: {ratio:.2f}%")
    
    # Decompress file
    success, message = file_compressor.decompress_file('sample_compressed.bin', 'sample_decompressed.txt')
    print(f"File decompression: {message}")
    
    # Verify integrity
    with open('sample.txt', 'r') as f1, open('sample_decompressed.txt', 'r') as f2:
        original = f1.read()
        decompressed = f2.read()
        print(f"File integrity check: {original == decompressed}")

# Binary data example
print("\n3. Binary Data Compression Example:")
binary_compressor = pb.HuffmanCompressor()

# Generate some binary data
binary_data = bytes([i % 256 for i in range(1000)])
print(f"Original binary data size: {len(binary_data)} bytes")

# Compress binary data
compressed_binary = binary_compressor.compress_bytes(binary_data)
print(f"Compressed binary size: {len(compressed_binary)} bytes")

# Decompress binary data
decompressed_binary = binary_compressor.decompress_bytes(compressed_binary)
print(f"Binary data integrity: {binary_data == decompressed_binary}")

# Show Huffman codes for a small example
print("\n4. Huffman Codes Example:")
small_compressor = pb.HuffmanCompressor()
test_data = b"abracadabra"
compressed = small_compressor.compress_bytes(test_data)

print("Huffman codes for 'abracadabra':")
for byte, code in sorted(small_compressor.codes.items()):
    char = chr(byte) if 32 <= byte <= 126 else f'0x{byte:02x}'
    print(f"  {char} (0x{byte:02x}): {code}")


# # Clean up sample files
# for file in ['sample.txt', 'sample_compressed.bin', 'sample_decompressed.txt']:
#     if os.path.exists(file):
#         os.remove(file)

# Advanced example
print("\n" + "="*50)
print("ADVANCED COMPRESSION STATISTICS")
print("="*50)

advanced_compressor = pb.AdvancedHuffmanCompressor()
test_text = "Hello, World! This is an advanced Huffman compression demonstration."
test_bytes = test_text.encode('utf-8')

advanced_compressor.print_detailed_stats(test_bytes)
