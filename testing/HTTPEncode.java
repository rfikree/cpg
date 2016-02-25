import java.net.URLEncoder;
import java.io.UnsupportedEncodingException;

public class HTTPEncode {
	public static void main(String[] args) {
		String URL = "_s=postalZip=H4P2D1";

		if (  args.length > 0 ) {
			URL = args[0];
		}

		System.out.println("URL: " + URL);
		try {
			URL = java.net.URLEncoder.encode(URL, "UTF-8");
			System.out.println("URL: " + URL);
		}
		catch ( UnsupportedEncodingException e ) {
			System.out.println("Failed to encode: " + URL);
			e.printStackTrace();
		}
	}
}
