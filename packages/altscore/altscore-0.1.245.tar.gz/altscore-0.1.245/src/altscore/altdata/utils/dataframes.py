import base64
import io


def df_to_base64(df):
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
