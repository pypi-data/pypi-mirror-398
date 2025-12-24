import qrcode

def show():
    """Display QR code for K Pandiyaraj's LinkedIn profile."""
    linkedin_url = "https://www.linkedin.com/in/pandiyaraj-k-49353467/"
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=2,
    )
    
    # Add data
    qr.add_data(linkedin_url)
    qr.make(fit=True)
    
    # Print to terminal
    qr.print_ascii(invert=True)
    
    # Print the URL below
    print(f"\n🔗 LinkedIn Profile: {linkedin_url}\n")
