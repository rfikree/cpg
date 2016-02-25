import java.net.URLDecoder;
import java.io.UnsupportedEncodingException;

public class HTTPDecode {
	public static void main(String[] args) {
		String URL = "/profile/rs/common/profile?_s=postalZip%3D%3DH4P2";
		String srcURL = null;
		int cycles = -1;

		if (  args.length > 0 ) {
			URL = args[0];
		}

		try {
			do {
				srcURL = URL;
				URL = java.net.URLDecoder.decode(srcURL, "UTF-8");
				cycles++;
			}	while ( ! URL.equals(srcURL));
		}
		catch ( UnsupportedEncodingException e ) {
			System.out.println("Failed to decode: " + URL);
			e.printStackTrace();
		}

		System.out.println(cycles + "-URL: " + URL);
	}
}
