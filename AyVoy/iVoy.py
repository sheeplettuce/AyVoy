import customtkinter as ctk
from PIL import Image
import os
from tkintermapview import TkinterMapView  # Importar la librería para el mapa interactivo
from tkinter import filedialog, messagebox
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from functools import partial

# Constants
ASSETS_PATH = r"C:\Python\AyVoy\INTER"
DATA_PATH = r"C:\Python\AyVoy\USERS"
ROUTES_PATH = r"C:\Python\AyVoy\ROUTES"
DOCS_PATH = r"C:\Python\AyVoy\TRAMITES"

@dataclass
class AppConfig:
    WINDOW_SIZE = "360x640"
    TITLE = "Ventana Principal"
    MAP_CENTER = (21.88234, -102.28259)
    MAP_ZOOM = 13
    BUTTON_STYLE = {
        "corner_radius": 20,
        "font": ("Arial Black", 14),
        "text_color": "white"
    }

class ResourceManager:
    def __init__(self):
        self._cached_images: Dict[str, ctk.CTkImage] = {}
    
    def get_image(self, path: str, size: Tuple[int, int]) -> ctk.CTkImage:
        cache_key = f"{path}_{size}"
        if cache_key not in self._cached_images:
            image = Image.open(path)
            image.thumbnail(size)
            self._cached_images[cache_key] = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=size
            )
        return self._cached_images[cache_key]

class DocumentManager:
    REQUIRED_DOCS = {
        "discapacitado": [
            "Acta de nacimiento", "CURP", "INE", 
            "Tarjeta DIF", "Foto Tamaño Infantil (Color)",
            "Comprobante de domicilio"
        ],
        "estudiante": [
            "Acta de nacimiento", "CURP", "INE",
            "Comprobante de Estudios", "Credencial Escolar",
            "Comprobante de domicilio"
        ],
        "adulto_mayor": [
            "Acta de nacimiento", "CURP", "INE",
            "Tarjeta INAPAM", "Comprobante de domicilio"
        ]
    }

    def create_doc_frame(self, parent, doc_type: str, folder_icon: ctk.CTkImage,
                        upload_callback) -> None:
        docs = self.REQUIRED_DOCS[doc_type]
        for doc in docs:
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(pady=5, padx=20, fill="x")
            
            ctk.CTkLabel(frame, text=doc, font=("Arial Black", 12)
                        ).pack(side="left", padx=10)
            
            ctk.CTkButton(frame, text="", image=folder_icon, 
                         width=30, height=30,
                         command=partial(upload_callback, doc)
                         ).pack(side="right", padx=10)

class RouteManager:
    def __init__(self):
        self._routes: Dict[str, List[Tuple[float, float]]] = {}
        self._descriptions: Dict[str, str] = {}
        self._load_routes()
        self._load_descriptions()

    def _load_routes(self):
        try:
            with open(f"{ROUTES_PATH}/rutas.txt", "r") as f:
                self._routes = {line.strip(): [] for line in f}
        except FileNotFoundError:
            print("Routes file not found")

    def _load_descriptions(self):
        try:
            with open(f"{ROUTES_PATH}/destinos.txt", "r", encoding="utf-8") as f:
                self._descriptions = dict(
                    line.strip().split(":", 1) for line in f if ":" in line
                )
        except FileNotFoundError:
            print("Descriptions file not found")

    def search_routes(self, query: str) -> List[str]:
        if not query:
            return list(self._routes.keys())
        return [r for r in self._routes if query.lower() in r.lower()]

class UIFactory:
    @staticmethod
    def create_button(parent, **kwargs) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            **{**AppConfig.BUTTON_STYLE, **kwargs}
        )

    @staticmethod
    def create_label(parent, **kwargs) -> ctk.CTkLabel:
        return ctk.CTkLabel(parent, **kwargs)

    @staticmethod
    def create_entry(parent, **kwargs) -> ctk.CTkEntry:
        return ctk.CTkEntry(parent, **kwargs)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Ventana Principal")
        self.root.geometry("360x640")
        self.root.configure(bg="#F5F5F5")  # Fondo agradable a la vista
        ctk.set_appearance_mode("light")  # Modo claro por defecto
        ctk.set_default_color_theme("blue")
        self.sesion_iniciada = False
        self.folio_actual = None  # Nueva variable para almacenar el folio
        self.Menu_Principal()

    def Menu_Principal(self):
        self.Limpiar_Ventana()
        
        # Cargar y redimensionar la imagen
        image_path = r"C:\Python\AyVoy\INTER\ayVOY.png"
        original_image = Image.open(image_path)
        original_image.thumbnail((200, 200))
        logo_image = ctk.CTkImage(
            light_image=original_image,
            dark_image=original_image,
            size=original_image.size
        )
        
        # Etiqueta con la imagen
        ctk.CTkLabel(self.root, image=logo_image, text="", bg_color="#F5F5F5").pack(pady=(130, 40))
        
        # Etiqueta de bienvenida
        ctk.CTkLabel(
            self.root,
            text="Bienvenido",
            font=("Bahnschrift Light", 22, "bold"),
            text_color="#0056b3",
            bg_color="#F5F5F5"
        ).pack(pady=10)
        
        # Botones
        UIFactory.create_button(self.root, text="Iniciar Sesión", command=self.Abrir_Menu).pack(pady=10, ipadx=10, ipady=5)
        UIFactory.create_button(self.root, text="Trámites", command=self.Abrir_Tramites).pack(pady=10, ipadx=10, ipady=5)
        UIFactory.create_button(self.root, text="Ver Mapa", command=self.Abrir_Mapa).pack(pady=10, ipadx=10, ipady=5)
        
        # Botón de cerrar sesión (visible solo si la sesión está iniciada)
        if self.sesion_iniciada:
            UIFactory.create_button(self.root, text="Cerrar Sesión", command=self.Cerrar_Sesion).pack(pady=10, ipadx=10, ipady=5)

    def Alternar_Modo_Oscuro(self):
        """Alterna entre modo claro y oscuro."""
        self.modo_oscuro = not self.modo_oscuro
        if self.modo_oscuro:
            ctk.set_appearance_mode("dark")
            self.root.configure(bg="#2E2E2E")  # Fondo oscuro
        else:
            ctk.set_appearance_mode("light")
            self.root.configure(bg="#F5F5F5")  # Fondo claro

        # Actualizar la página actual con el nuevo fondo
        self.Limpiar_Ventana()
        self.Menu_Principal()

    def Abrir_Menu(self):
        self.Limpiar_Ventana()
        
        ctk.CTkLabel(self.root, text="Iniciar Sesión", font=("Arial", 16), text_color="#0056b3").pack(pady=10)
        ctk.CTkLabel(self.root, text="Folio: ", text_color="#0056b3").pack(pady=5)
        
        # Entrada de texto para el folio con binding de Enter
        self.folio_entry = UIFactory.create_entry(self.root)
        self.folio_entry.pack(pady=5)
        self.folio_entry.bind("<Return>", lambda event: self.Validar_Folio())  # Al dar Enter, valida el folio
        self.folio_entry.focus()  # Dar foco al campo de entrada
        
        # Etiqueta para mensajes de error
        self.error_label = ctk.CTkLabel(self.root, text="", font=("Arial", 12), text_color="red")
        self.error_label.pack(pady=5)
        
        # Botones
        UIFactory.create_button(self.root, text="Ingresar", command=self.Validar_Folio).pack(pady=10, ipadx=10, ipady=5)
        UIFactory.create_button(self.root, text="Regresar", command=self.Menu_Principal).pack(pady=10, ipadx=10, ipady=5)
    
    def Validar_Folio(self):
        folio = self.folio_entry.get().strip()
        archivo_path = r"C:\Python\AyVoy\USERS\usuarios.txt"
        
        try:
            with open(archivo_path, "r") as archivo:
                folios = [line.strip().split(',')[0] for line in archivo.readlines()]
            
            if folio in folios:
                self.sesion_iniciada = True
                self.folio_actual = folio  # Guardar el folio actual
                self.Abrir_Mapa()
            else:
                self.error_label.configure(text="Folio incorrecto. Intente de nuevo.", text_color="red")
        except FileNotFoundError:
            self.error_label.configure(text="Error: Archivo de usuarios no encontrado.", text_color="red")
    
    def Abrir_Mapa(self):
        self.Limpiar_Ventana()
        
        # Título
        ctk.CTkLabel(self.root, text="Busca tu ruta!", font=("Arial", 16), text_color="#0056b3").pack(pady=10)
        
        # Frame para el buscador y el botón de saldo
        search_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        search_frame.pack(pady=5)
        
        # Entrada de texto para buscar rutas
        self.search_entry = UIFactory.create_entry(search_frame, placeholder_text="Buscar ruta...")
        self.search_entry.pack(side="left", pady=5)
        self.search_entry.bind("<KeyRelease>", self.Buscar_Rutas)
        self.search_entry.focus()
        
        # Botón de saldo (solo visible si la sesión está iniciada)
        if self.sesion_iniciada:
            try:
                dinero_path = r"C:\Python\AyVoy\INTER\DINERO.png"
                if os.path.exists(dinero_path):
                    dinero_image = Image.open(dinero_path)
                    # Calcular dimensiones manteniendo proporción
                    original_width, original_height = dinero_image.size
                    target_height = 40  # Altura deseada
                    aspect_ratio = original_width / original_height
                    target_width = int(target_height * aspect_ratio)
                    
                    dinero_icon = ctk.CTkImage(
                        light_image=dinero_image,
                        dark_image=dinero_image,
                        size=(target_width, target_height)
                    )
                    
                    saldo_button = ctk.CTkButton(
                        search_frame,
                        text="",
                        image=dinero_icon,
                        command=self.Abrir_Saldo,
                        fg_color="transparent",
                        hover_color="#E5E5E5",
                        width=target_width,
                        height=target_height
                    )
                    saldo_button.pack(side="left", padx=10)
            except Exception as e:
                print(f"Error al cargar el ícono de saldo: {e}")
        
        # Lista desplegable para mostrar resultados
        self.result_dropdown = ctk.CTkOptionMenu(
            self.root, 
            values=["Selecciona una ruta"], 
            width=300,
            command=self.Mostrar_Descripcion_Ruta
        )
        self.result_dropdown.pack(pady=5)
        
        # Mapa interactivo
        self.map_widget = TkinterMapView(self.root, width=360, height=300, corner_radius=0)
        self.map_widget.pack(pady=10)
        self.map_widget.set_position(21.88234, -102.28259)
        self.map_widget.set_zoom(13)
        
        # Etiqueta para mostrar la descripción de la ruta
        self.descripcion_label = ctk.CTkLabel(
            self.root, 
            text="", 
            font=("Arial", 12), 
            text_color="#0056b3", 
            wraplength=300
        )
        self.descripcion_label.pack(pady=10)
        
        # Botones
        UIFactory.create_button(
            self.root, 
            text="Regresar",
            command=self.Menu_Principal
        ).pack(pady=10)
        
        # Botón de cerrar sesión (visible solo si la sesión está iniciada)
        if self.sesion_iniciada:
            UIFactory.create_button(
                self.root, 
                text="Cerrar Sesión",
                command=self.Cerrar_Sesion
            ).pack(pady=10)
        
        # Cargar las rutas después de crear el dropdown
        self.Cargar_Rutas()

    def Cargar_Rutas(self):
        """Carga las rutas desde el archivo"""
        archivo_path = r"C:\Python\AyVoy\ROUTES\rutas.txt"
        try:
            with open(archivo_path, "r") as archivo:
                rutas = [line.strip() for line in archivo.readlines()]
                self.result_dropdown.configure(values=rutas)
                self.result_dropdown.set("Selecciona una ruta")
        except FileNotFoundError:
            self.result_dropdown.configure(values=["Error: Archivo no encontrado"])
            self.result_dropdown.set("Error: Archivo no encontrado")

    def Mostrar_Descripcion_Ruta(self, ruta_seleccionada):
        archivo_path = r"C:\Python\AyVoy\ROUTES\destinos.txt"
        try:
            with open(archivo_path, "r", encoding="utf-8") as archivo:
                lineas = archivo.readlines()
                descripciones = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in lineas}
                
                # Mostrar la descripción de la ruta seleccionada
                if ruta_seleccionada in descripciones:
                    self.descripcion_label.configure(text=descripciones[ruta_seleccionada])
                    self.Dibujar_Ruta(ruta_seleccionada)  # Dibujar la ruta en el mapa
                else:
                    self.descripcion_label.configure(text="Descripción no disponible.")
        except FileNotFoundError:
            self.descripcion_label.configure(text="Error: Archivo de descripciones no encontrado.")

    def Buscar_Rutas(self, event):
        query = self.search_entry.get().strip().lower()
        archivo_path = r"C:\Python\AyVoy\ROUTES\rutas.txt"
        
        try:
            with open(archivo_path, "r") as archivo:
                rutas = [line.strip() for line in archivo.readlines()]
            
            # Si el buscador está vacío, mostrar todas las rutas
            if not query:
                self.result_dropdown.configure(values=rutas)
                self.result_dropdown.set("Selecciona una ruta")
            else:
                # Filtrar rutas que coincidan con la búsqueda
                resultados = [ruta for ruta in rutas if query in ruta.lower()]
                
                # Actualizar la lista desplegable con los resultados
                if resultados:
                    self.result_dropdown.configure(values=resultados)
                    self.result_dropdown.set(resultados[0])  # Seleccionar el primer resultado
                else:
                    self.result_dropdown.configure(values=["No hay coincidencias"])
                    self.result_dropdown.set("No hay coincidencias")
        except FileNotFoundError:
            self.result_dropdown.configure(values=["Error: Archivo no encontrado"])
            self.result_dropdown.set("Error: Archivo no encontrado")
    
    def Dibujar_Ruta(self, ruta_seleccionada):
        # Diccionario con coordenadas aproximadas de las rutas
        rutas_coordenadas = {
            "Ruta 1": [(21.88234, -102.28259), (21.885, -102.29)],  # Ojocaliente al centro
            "Ruta 2": [(21.885, -102.29), (21.88, -102.28)],  # Morelos al centro
            "Ruta 3": [(21.88, -102.28), (21.88234, -102.28259)],  # Insurgentes al centro
            "Ruta 4": [(21.88234, -102.28259), (21.886, -102.27)],  # Héroes al centro
            "Ruta 5": [(21.88234, -102.28259), (21.88, -102.26)],  # Pilar Blanco al centro
            "Ruta 6": [(21.88234, -102.28259), (21.89, -102.25)],  # Villas de Nuestra Señora de la Asunción al centro
            "Ruta 7": [(21.88234, -102.28259), (21.88, -102.24)],  # Mirador de las Culturas al centro
            "Ruta 8": [(21.88234, -102.28259), (21.87, -102.23)],  # Lomas del Ajedrez al centro
            "Ruta 9": [(21.88234, -102.28259), (21.86, -102.22)],  # Villa Montaña al centro
            "Ruta 10": [(21.88234, -102.28259), (21.85, -102.21)],  # Villas del Puertecito al centro
            "Ruta 11": [(21.88234, -102.28259), (21.84, -102.20)],  # Municipio Libre al centro
            "Ruta 12": [(21.88234, -102.28259), (21.83, -102.19)],  # Valle de los Cactus al centro
            "Ruta 14": [(21.88234, -102.28259), (21.82, -102.18)],  # Rodolfo Landeros al centro
            "Ruta 16": [(21.88234, -102.28259), (21.81, -102.17)],  # Villas de la Cantera al centro
            "Ruta 18": [(21.88234, -102.28259), (21.80, -102.16)],  # Villa Teresa al centro
            "Ruta 19": [(21.88234, -102.28259), (21.79, -102.15)],  # Colinas del Río al fraccionamiento Morelos
            "Ruta 20N": [(21.88234, -102.28259), (21.88, -102.28), (21.89, -102.29)],  # Circuito Primer Anillo Norte
            "Ruta 20S": [(21.88234, -102.28259), (21.87, -102.27), (21.86, -102.26)],  # Circuito Primer Anillo Sur
            "Ruta 23": [(21.88234, -102.28259), (21.89, -102.25)],  # Villas de Nuestra Señora de la Asunción al centro
            "Ruta 24": [(21.88234, -102.28259), (21.88, -102.24)],  # Jesús Terán al centro
            "Ruta 25": [(21.88234, -102.28259), (21.87, -102.23)],  # Villa de las Palmas al centro
            "Ruta 27": [(21.88234, -102.28259), (21.86, -102.22)],  # Lomas del Mirador al centro
            "Ruta 28": [(21.88234, -102.28259), (21.85, -102.21)],  # Los Pericos al centro
            "Ruta 29": [(21.88234, -102.28259), (21.84, -102.20)],  # Villas de Nuestra Señora de la Asunción Sector Guadalupe al centro
            "Ruta 30": [(21.88234, -102.28259), (21.83, -102.19)],  # Villa Montaña al centro
            "Ruta 33": [(21.88234, -102.28259), (21.82, -102.18)],  # Villa Taurina al centro
            "Ruta 34": [(21.88234, -102.28259), (21.81, -102.17)],  # Vistas del Sol al centro
            "Ruta 35": [(21.88234, -102.28259), (21.80, -102.16)],  # Villa de las Norias al centro
            "Ruta 40": [(21.88234, -102.28259), (21.89, -102.29), (21.88, -102.28)],  # Segundo Anillo de Circunvalación
            "Ruta 50": [(21.88234, -102.28259), (21.87, -102.27), (21.86, -102.26)],  # Tercer Anillo de Circunvalación
            "Ruta Especial UTR": [(21.88234, -102.28259), (21.85, -102.21)],  # Universidad Tecnológica de Aguascalientes
        }
        
        # Limpiar marcadores y rutas anteriores
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        
        # Verificar si la ruta seleccionada tiene coordenadas
        if ruta_seleccionada in rutas_coordenadas:
            coordenadas = rutas_coordenadas[ruta_seleccionada]
            
            # Agregar marcadores en los puntos de la ruta
            for lat, lon in coordenadas:
                self.map_widget.set_marker(lat, lon, text=f"Punto ({lat}, {lon})")
            
            # Dibujar la línea de la ruta
            self.map_widget.set_path(coordenadas, color="red", width=3)
        else:
            print("Ruta no encontrada o sin coordenadas definidas.")

    def Abrir_Tramites(self):
        self.Limpiar_Ventana()
        
        # Título del menú
        ctk.CTkLabel(self.root, text="Trámites", font=("Arial", 20, "bold"), 
                     text_color="#0056b3").pack(pady=20)
        
        # Botones de trámites
        UIFactory.create_button(self.root, text="Tarjeta Discapacitado", 
                     command=self.Tarjeta_Discapacitado).pack(pady=10, ipadx=10, ipady=5)
        
        UIFactory.create_button(self.root, text="Tarjeta Adulto Mayor",
                     command=self.Tarjeta_Adulto_Mayor).pack(pady=10, ipadx=10, ipady=5)
        
        UIFactory.create_button(self.root, text="Tarjeta Estudiante",
                     command=self.Tarjeta_Estudiante).pack(pady=10, ipadx=10, ipady=5)
        
        # Botón de regresar
        UIFactory.create_button(self.root, text="Regresar",
                     command=self.Menu_Principal).pack(pady=20, ipadx=10, ipady=5)

    def Tarjeta_Discapacitado(self):
        self.Limpiar_Ventana()
        
        # Título
        ctk.CTkLabel(self.root, text="Documentos Requeridos", 
                     font=("Arial", 20, "bold"), text_color="#0056b3").pack(pady=10)
        
        # Cargar icono de carpeta
        folder_path = r"C:\Python\AyVoy\INTER\FOLDER.png"
        folder_image = Image.open(folder_path)
        folder_image.thumbnail((30, 30))
        folder_icon = ctk.CTkImage(light_image=folder_image, dark_image=folder_image, size=(30, 30))
        
        # Crear frames de documentos
        doc_manager = DocumentManager()
        doc_manager.create_doc_frame(self.root, "discapacitado", folder_icon, self.Subir_Documento)
        
        # Sección de reactivación
        ctk.CTkLabel(self.root, text="En caso de ser reactivación:", 
                     font=("Arial", 14), text_color="red").pack(pady=(20,5))
        
        # Frame para Tarjeta Soluciones YOVOY
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(frame, text="Tarjeta Soluciones YOVOY", 
                     font=("Arial Black", 12)).pack(side="left", padx=10)
        ctk.CTkButton(frame, text="", image=folder_icon, width=30, height=30,
                     command=lambda: self.Subir_Documento("Tarjeta YOVOY")).pack(side="right", padx=10)
        
        # Botón de regresar
        UIFactory.create_button(self.root, text="Regresar", command=self.Abrir_Tramites).pack(pady=20)
        self.root.bind("<Return>", lambda event: self.Abrir_Tramites())  # Agregar binding de Enter al último botón de documento

    def Tarjeta_Estudiante(self):
        self.Limpiar_Ventana()
        
        # Título
        ctk.CTkLabel(self.root, text="Documentos Requeridos", 
                     font=("Arial", 20, "bold"), text_color="#0056b3").pack(pady=10)
        
        # Cargar icono de carpeta
        folder_path = r"C:\Python\AyVoy\INTER\FOLDER.png"
        folder_image = Image.open(folder_path)
        folder_image.thumbnail((30, 30))
        folder_icon = ctk.CTkImage(light_image=folder_image, dark_image=folder_image, size=(30, 30))
        
        # Crear frames de documentos
        doc_manager = DocumentManager()
        doc_manager.create_doc_frame(self.root, "estudiante", folder_icon, self.Subir_Documento)
        
        # Sección de reactivación
        ctk.CTkLabel(self.root, text="En caso de ser reactivación:", 
                     font=("Arial", 14), text_color="red").pack(pady=(20,5))
        
        # Frame para Tarjeta Soluciones YOVOY
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(frame, text="Tarjeta Soluciones YOVOY", 
                     font=("Arial Black", 12)).pack(side="left", padx=10)
        ctk.CTkButton(frame, text="", image=folder_icon, width=30, height=30,
                     command=lambda: self.Subir_Documento("Tarjeta YOVOY")).pack(side="right", padx=10)
        
        # Botón de regresar
        UIFactory.create_button(self.root, text="Regresar", command=self.Abrir_Tramites).pack(pady=20)
        self.root.bind("<Return>", lambda event: self.Abrir_Tramites())  # Agregar binding de Enter al último botón de documento

    def Tarjeta_Adulto_Mayor(self):
        self.Limpiar_Ventana()
        
        # Título
        ctk.CTkLabel(self.root, text="Documentos Requeridos", 
                     font=("Arial", 20, "bold"), text_color="#0056b3").pack(pady=10)
        
        # Cargar icono de carpeta
        folder_path = r"C:\Python\AyVoy\INTER\FOLDER.png"
        folder_image = Image.open(folder_path)
        folder_image.thumbnail((30, 30))  # Redimensionar a 30x30 manteniendo proporción
        folder_icon = ctk.CTkImage(light_image=folder_image, dark_image=folder_image, size=(30, 30))
        
        # Crear frames de documentos
        doc_manager = DocumentManager()
        doc_manager.create_doc_frame(self.root, "adulto_mayor", folder_icon, self.Subir_Documento)
        
        # Botón de regresar
        UIFactory.create_button(self.root, text="Regresar", command=self.Abrir_Tramites).pack(pady=20)
        self.root.bind("<Return>", lambda event: self.Abrir_Tramites())  # Agregar binding de Enter al último botón de documento

    def Subir_Documento(self, tipo_documento):
        # Abrir diálogo para seleccionar archivo
        archivo = filedialog.askopenfile(
            title=f"Seleccionar {tipo_documento}",
            filetypes=[
                ("Archivos PDF", "*.pdf"),
                ("Imágenes", "*.png *.jpg *.jpeg")
            ]
        )
        
        if archivo:
            # Crear directorio de trámites si no existe
            tramites_dir = r"C:\Python\AyVoy\TRAMITES"
            if not os.path.exists(tramites_dir):
                os.makedirs(tramites_dir)
            
            # Copiar archivo a la carpeta de trámites
            nombre_archivo = f"{tipo_documento}_{os.path.basename(archivo.name)}"
            destino = os.path.join(tramites_dir, nombre_archivo)
            
            try:
                with open(archivo.name, 'rb') as f_origen:
                    with open(destino, 'wb') as f_destino:
                        f_destino.write(f_origen.read())
                messagebox.showinfo("Éxito", f"Documento {tipo_documento} subido correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al subir el documento: {str(e)}")

    def Limpiar_Ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def Seleccionar_Primera_Ruta(self, event):
        # Obtener valores actuales del dropdown
        valores = self.result_dropdown.cget("values")
        if valores and valores[0] != "No hay coincidencias" and valores[0] != "Error: Archivo no encontrado":
            # Seleccionar primera ruta y mostrar su descripción
            self.result_dropdown.set(valores[0])
            self.Mostrar_Descripcion_Ruta(valores[0])

    def Abrir_Saldo(self):
        self.Limpiar_Ventana()
        
        # Título del menú
        ctk.CTkLabel(self.root, text="Saldo Actual", 
                     font=("Arial", 24, "bold"), 
                     text_color="#0056b3").pack(pady=(50, 20))
        
        # Frame principal para el contenido
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20)
        
        # Obtener el saldo y movimientos del usuario actual
        archivo_path = r"C:\Python\AyVoy\USERS\usuarios.txt"
        try:
            with open(archivo_path, "r") as archivo:
                usuario_encontrado = False
                for linea in archivo:
                    datos = linea.strip().split(",")
                    if len(datos) >= 2 and datos[0].strip() == self.folio_actual:
                        usuario_encontrado = True
                        # Mostrar saldo actual
                        saldo = datos[1].strip()
                        ctk.CTkLabel(main_frame, 
                                   text=f"${saldo}", 
                                   font=("Arial Black", 36),
                                   text_color="#2E7D32").pack(pady=20)
                        
                        # Título de movimientos
                        ctk.CTkLabel(main_frame, 
                                   text="Movimientos realizados",
                                   font=("Arial", 18, "bold"),
                                   text_color="#0056b3").pack(pady=(20, 10))
                        
                        # Frame para la lista de movimientos con scroll
                        movimientos_frame = ctk.CTkScrollableFrame(main_frame, 
                                                                 width=300, 
                                                                 height=200,
                                                                 fg_color="#F0F0F0")
                        movimientos_frame.pack(pady=10, fill="both", expand=True)
                        
                        # Mostrar cada movimiento
                        if len(datos) > 2:
                            for movimiento in datos[2:]:
                                movimiento = movimiento.strip()
                                if movimiento:  # Solo si el movimiento no está vacío
                                    ctk.CTkLabel(movimientos_frame,
                                               text=movimiento,
                                               font=("Arial", 12),
                                               text_color="#333333").pack(
                                                   pady=5, 
                                                   padx=10, 
                                                   anchor="w"
                                               )
                        else:
                            ctk.CTkLabel(movimientos_frame,
                                       text="No hay movimientos registrados",
                                       font=("Arial", 12),
                                       text_color="#666666").pack(pady=10)
                        break
                
                if not usuario_encontrado:
                    ctk.CTkLabel(main_frame, 
                               text="Usuario no encontrado. Verifica tu folio.", 
                               font=("Arial", 16),
                               text_color="red").pack(pady=20)
        except FileNotFoundError:
            ctk.CTkLabel(main_frame, 
                        text="Error: Archivo de usuarios no encontrado", 
                        font=("Arial", 16),
                        text_color="red").pack(pady=20)
        
        # Botón de recargar tarjeta
        UIFactory.create_button(self.root, 
                      text="Recargar Tarjeta", 
                      command=self.Recargar_Tarjeta).pack(pady=10)

        # Botón de regresar
        UIFactory.create_button(self.root, 
                      text="Regresar", 
                      command=self.Abrir_Mapa).pack(pady=20)

    def Recargar_Tarjeta(self):
        self.Limpiar_Ventana()
        
        # Título del menú
        ctk.CTkLabel(self.root, text="Recargar Tarjeta", 
                     font=("Arial", 24, "bold"), 
                     text_color="#0056b3").pack(pady=(20, 10))
        
        # Entrada para el número de tarjeta
        ctk.CTkLabel(self.root, text="Número de Tarjeta:", 
                     font=("Arial", 16), 
                     text_color="#0056b3").pack(pady=5)
        tarjeta_entry = UIFactory.create_entry(self.root)
        tarjeta_entry.pack(pady=5)
        
        # Entrada para la fecha de expiración
        ctk.CTkLabel(self.root, text="Fecha de Expiración (MM/AA):", 
                     font=("Arial", 16), 
                     text_color="#0056b3").pack(pady=5)
        expiracion_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        expiracion_frame.pack(pady=5)
        mes_entry = UIFactory.create_entry(expiracion_frame, width=50, placeholder_text="MM")
        mes_entry.pack(side="left", padx=5)
        anio_entry = UIFactory.create_entry(expiracion_frame, width=50, placeholder_text="AA")
        anio_entry.pack(side="left", padx=5)
        
        # Entrada para el titular de la tarjeta
        ctk.CTkLabel(self.root, text="Titular de la Tarjeta:", 
                     font=("Arial", 16), 
                     text_color="#0056b3").pack(pady=5)
        titular_entry = UIFactory.create_entry(self.root)
        titular_entry.pack(pady=5)
        
        # Entrada para el código de seguridad
        ctk.CTkLabel(self.root, text="Código de Seguridad (CVV):", 
                     font=("Arial", 16), 
                     text_color="#0056b3").pack(pady=5)
        cvv_entry = UIFactory.create_entry(self.root, show="*")
        cvv_entry.pack(pady=5)
        
        # Entrada para el monto a recargar
        ctk.CTkLabel(self.root, text="Monto a Recargar:", 
                     font=("Arial", 16), 
                     text_color="#0056b3").pack(pady=5)
        monto_entry = UIFactory.create_entry(self.root)
        monto_entry.pack(pady=5)
        
        # Checkbox para guardar los datos de la tarjeta
        guardar_datos_var = ctk.BooleanVar()
        guardar_datos_checkbox = ctk.CTkCheckBox(
            self.root, 
            text="Guardar los datos de esta tarjeta para pagos futuros", 
            variable=guardar_datos_var
        )
        guardar_datos_checkbox.pack(pady=10)
        
        # Botón para confirmar la recarga
        def confirmar_recarga():
            numero_tarjeta = tarjeta_entry.get().strip()
            mes = mes_entry.get().strip()
            anio = anio_entry.get().strip()
            titular = titular_entry.get().strip()
            cvv = cvv_entry.get().strip()
            monto = monto_entry.get().strip()
            
            if not all([numero_tarjeta, mes, anio, titular, cvv, monto]):
                messagebox.showerror("Error", "Por favor, completa todos los campos.")
                return
            
            try:
                monto = float(monto)
                if monto <= 0:
                    raise ValueError("El monto debe ser mayor a 0.")
            except ValueError:
                messagebox.showerror("Error", "Ingresa un monto válido.")
                return
            
            # Aquí puedes agregar lógica para procesar el pago con los datos ingresados
            
            # Actualizar el saldo en el archivo
            archivo_path = r"C:\Python\AyVoy\USERS\usuarios.txt"
            try:
                with open(archivo_path, "r") as archivo:
                    lineas = archivo.readlines()
                
                with open(archivo_path, "w") as archivo:
                    for linea in lineas:
                        datos = linea.strip().split(",")
                        if len(datos) >= 2 and datos[0].strip() == self.folio_actual:
                            saldo_actual = float(datos[1].strip())
                            nuevo_saldo = saldo_actual + monto
                            datos[1] = f"{nuevo_saldo:.2f}"
                            archivo.write(",".join(datos) + "\n")
                            messagebox.showinfo("Éxito", f"Se recargaron ${monto:.2f} correctamente.")
                        else:
                            archivo.write(linea)
            except FileNotFoundError:
                messagebox.showerror("Error", "Archivo de usuarios no encontrado.")
                return
            
            # Regresar al menú de saldo
            self.Abrir_Saldo()
        
        UIFactory.create_button(self.root, 
                      text="Confirmar Recarga", 
                      command=confirmar_recarga).pack(pady=10)

        # Botón de regresar
        UIFactory.create_button(self.root, 
                      text="Regresar", 
                      command=self.Abrir_Saldo).pack(pady=20)

    def Cerrar_Sesion(self):
        """Cierra la sesión del usuario y regresa al menú principal."""
        self.sesion_iniciada = False
        self.folio_actual = None
        messagebox.showinfo("Sesión Cerrada", "Has cerrado sesión correctamente.")
        self.Menu_Principal()

if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()
