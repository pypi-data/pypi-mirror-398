import PyPDF2
import sys

def combine_pdfs(args):
    pdf_list=args.i
    output_filename=args.o
    merger = PyPDF2.PdfMerger()
    
    for pdf in pdf_list:
        merger.append(pdf)
    
    merger.write(output_filename)
    merger.close()
    print(f"Combined PDF saved as: {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combine_pdfs.py output.pdf input1.pdf input2.pdf ...")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    combine_pdfs(input_files, output_file)
