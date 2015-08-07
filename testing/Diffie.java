import java.security.AlgorithmParameterGenerator;
import java.security.InvalidParameterException;

public class Diffie {
    public static void main (String[] args) throws Exception {
        AlgorithmParameterGenerator apg = AlgorithmParameterGenerator . getInstance ("DiffieHellman");
        int good = 0;
        for (int i = 512  ;  i <= 16384  ;  i += 64) {
            try {
                apg . init (i);
            } catch (InvalidParameterException e) {
                break;
            }
            good = i;
        }
        System . out . println ("maximum DH size is " + good);
    }
}
