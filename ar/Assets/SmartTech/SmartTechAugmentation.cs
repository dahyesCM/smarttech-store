using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class SmartTechAugmentation : MonoBehaviour
{
    public enum ProductModel { Keyboard, Laptop }

    [SerializeField] private ProductModel model = ProductModel.Keyboard;
    [SerializeField] private string apiBase = "http://127.0.0.1:8000";
    [SerializeField] private float targetWidthMeters = 0.20f;

    private GameObject content;
    private string caption;
    private bool loading;

    [Serializable]
    private class Product
    {
        public string name;
        public string price;
    }

    private void Awake()
    {
        var origin = new GameObject("Modelo SmartTech");
        origin.transform.SetParent(transform, false);
        origin.transform.localScale = Vector3.one * (targetWidthMeters / 0.20f);
        content = origin;
        if (model == ProductModel.Keyboard)
            BuildKeyboard(content.transform);
        else
            BuildLaptop(content.transform);
        content.SetActive(false);
    }

    public void ShowProduct()
    {
        content.SetActive(true);
        if (!loading && string.IsNullOrEmpty(caption))
            StartCoroutine(FetchProduct());
    }

    public void HideProduct()
    {
        content.SetActive(false);
    }

    private IEnumerator FetchProduct()
    {
        loading = true;
        string sku = model == ProductModel.Keyboard ? "teclado" : "laptop";
        using (var request = UnityWebRequest.Get(apiBase.TrimEnd('/') + "/api/products/" + sku + "/"))
        {
            request.timeout = 8;
            yield return request.SendWebRequest();
#if UNITY_2020_2_OR_NEWER
            if (request.result == UnityWebRequest.Result.Success)
#else
            if (!request.isNetworkError && !request.isHttpError)
#endif
            {
                var product = JsonUtility.FromJson<Product>(request.downloadHandler.text);
                caption = product.name + " · S/ " + product.price;
            }
            else
                Debug.LogWarning("API SmartTech: " + request.error);
        }
        loading = false;
    }

    private void OnGUI()
    {
        if (content != null && content.activeInHierarchy)
            GUI.Label(new Rect(16, 16, 460, 32),
                caption ?? (loading ? "Cargando producto…" : "Catálogo temporalmente no disponible."));
    }

    private static void BuildKeyboard(Transform parent)
    {
        var shell = new Color(0.16f, 0.17f, 0.22f);
        Part(parent, "Carcasa", new Vector3(0, .006f, 0), new Vector3(.146f, .012f, .062f), shell);
        for (int row = 0; row < 5; row++)
        {
            for (int column = 0; column < 12; column++)
            {
                var position = new Vector3((column - 5.5f) * .0115f, .015f, (row - 2) * .0105f);
                Color color = column == 0 || column == 11 ? new Color(.51f, .35f, .78f) : Color.white;
                Part(parent, "Tecla", position, new Vector3(.0095f, .006f, .0085f), color);
            }
        }
    }

    private static void BuildLaptop(Transform parent)
    {
        var shell = new Color(.5f, .54f, .65f);
        var screen = new Vector3(0, .05f, .045f);
        Part(parent, "Base", new Vector3(0, .004f, 0), new Vector3(.145f, .008f, .095f), shell);
        Part(parent, "Teclado", new Vector3(0, .009f, .018f), new Vector3(.118f, .003f, .04f), Color.black);
        Part(parent, "Panel táctil", new Vector3(0, .009f, -.025f), new Vector3(.042f, .002f, .022f), Color.gray);
        Part(parent, "Tapa", screen, new Vector3(.145f, .09f, .006f), shell);
        Part(parent, "Pantalla", screen + Vector3.back * .004f,
            new Vector3(.132f, .078f, .002f), new Color(.14f, .20f, .46f));
    }

    private static void Part(Transform parent, string label, Vector3 position, Vector3 size, Color color)
    {
        var part = GameObject.CreatePrimitive(PrimitiveType.Cube);
        part.name = label;
        part.transform.SetParent(parent, false);
        part.transform.localPosition = position;
        part.transform.localScale = size;
        Destroy(part.GetComponent<Collider>());
        var properties = new MaterialPropertyBlock();
        properties.SetColor("_Color", color);
        properties.SetColor("_BaseColor", color);
        part.GetComponent<Renderer>().SetPropertyBlock(properties);
    }
}
