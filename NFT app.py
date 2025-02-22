import streamlit as st
from PIL import Image
import random
import json
import io
import zipfile

st.title("NFT Generator App")

# ▸ Parámetros de generación en la barra lateral
num_nfts = st.sidebar.number_input("Cantidad de NFTs a generar", min_value=1, max_value=10000, value=10)
full_set_prob = st.sidebar.slider("Probabilidad de Full Set", 0.0, 1.0, 0.05)
shiny_prob = st.sidebar.slider("Probabilidad de Shiny Weapon", 0.0, 1.0, 0.069)

st.header("Sube tus Assets")

# ▸ Archivos únicos
background_file = st.file_uploader("Sube el fondo (PNG)", type=["png"])
body_file = st.file_uploader("Sube el cuerpo (PNG)", type=["png"])

st.subheader("Sube los Traits (PNG)")
boots_files = st.file_uploader("Sube los traits de Boots", type=["png"], accept_multiple_files=True)
clothing_files = st.file_uploader("Sube los traits de Clothing (se mostrarán como Armor)", type=["png"], accept_multiple_files=True)
eyes_files = st.file_uploader("Sube los traits de Eyes", type=["png"], accept_multiple_files=True)
gloves_files = st.file_uploader("Sube los traits de Gloves", type=["png"], accept_multiple_files=True)
helmet_files = st.file_uploader("Sube los traits de Helmet", type=["png"], accept_multiple_files=True)
weapon_files = st.file_uploader("Sube los traits de Weapon", type=["png"], accept_multiple_files=True)
shiny_weapon_files = st.file_uploader("Sube las versiones Shiny de Weapon (opcional)", type=["png"], accept_multiple_files=True)

# ▸ Verificar que se hayan subido los assets requeridos
if not background_file or not body_file or not (boots_files and clothing_files and eyes_files and gloves_files and helmet_files and weapon_files):
    st.warning("Por favor, sube todos los assets requeridos: fondo, cuerpo y traits para Boots, Clothing, Eyes, Gloves, Helmet y Weapon.")
    st.stop()

# ▸ Función para cargar archivos subidos y guardarlos en un diccionario {nombre: imagen}
def load_uploaded_files(file_list):
    assets_dict = {}
    for file in file_list:
        file.seek(0)
        try:
            img = Image.open(file).convert("RGBA")
            assets_dict[file.name] = img
        except Exception as e:
            st.error(f"Error cargando la imagen {file.name}: {e}")
    return assets_dict

# ▸ Cargar cada asset
try:
    assets = {}
    assets["background"] = Image.open(background_file).convert("RGBA")
    assets["body"] = Image.open(body_file).convert("RGBA")
    assets["boots"] = load_uploaded_files(boots_files)
    assets["clothing"] = load_uploaded_files(clothing_files)
    assets["eyes"] = load_uploaded_files(eyes_files)
    assets["gloves"] = load_uploaded_files(gloves_files)
    assets["helmet"] = load_uploaded_files(helmet_files)
    assets["weapon"] = load_uploaded_files(weapon_files)
    assets["shiny_weapon"] = load_uploaded_files(shiny_weapon_files) if shiny_weapon_files else {}
except Exception as e:
    st.error(f"Error al cargar los assets: {e}")
    st.stop()

# ▸ Función para generar un NFT y su metadata
def generate_nft(nft_number, assets, full_set_prob, shiny_prob):
    try:
        is_full_set = random.random() < full_set_prob
        is_shiny = False

        metadata = {
            "name": f"PRIMO #{nft_number:04d}",
            "description": "Primo from the stone age collection",
            "external_url": "https://your-nft-site.com",
            "image": "",  # Se completará luego
            "attributes": []
        }

        trait_keys = ["boots", "clothing", "eyes", "gloves", "helmet", "weapon"]
        selected_traits = {}

        # ▸ Calcular la intersección de set names (prefijos antes del "_") para full set
        available_sets = None
        for trait in trait_keys:
            trait_set_names = set()
            for fname in assets[trait].keys():
                if "_" in fname:
                    prefix = fname.split("_")[0].lower()
                    trait_set_names.add(prefix)
            if available_sets is None:
                available_sets = trait_set_names
            else:
                available_sets = available_sets.intersection(trait_set_names)

        if is_full_set and available_sets and len(available_sets) > 0:
            chosen_set = random.choice(list(available_sets))
            for trait in trait_keys:
                if trait == "clothing":
                    target_fname = f"{chosen_set.upper()}_ARMOR.png"
                else:
                    target_fname = f"{chosen_set.upper()}_{trait.upper()}.png"
                if target_fname in assets[trait]:
                    selected_traits[trait] = target_fname
                else:
                    selected_traits[trait] = random.choice(list(assets[trait].keys()))
            full_set_flag = True
        else:
            for trait in trait_keys:
                selected_traits[trait] = random.choice(list(assets[trait].keys()))
            full_set_flag = False

        # ▸ Determinar si se activa shiny weapon
        if random.random() < shiny_prob:
            weapon_fname = selected_traits["weapon"]
            if weapon_fname in assets["shiny_weapon"]:
                selected_traits["weapon"] = weapon_fname
                is_shiny = True

        # ▸ Crear la imagen final combinando las capas
        nft_img = assets["background"].copy()

        # 1. Weapon (debajo del cuerpo)
        if selected_traits.get("weapon") in assets["weapon"]:
            if is_shiny and selected_traits["weapon"] in assets["shiny_weapon"]:
                weapon_img = assets["shiny_weapon"][selected_traits["weapon"]]
            else:
                weapon_img = assets["weapon"][selected_traits["weapon"]]
            nft_img.paste(weapon_img, (0, 0), weapon_img)

        # 2. Cuerpo
        nft_img.paste(assets["body"], (0, 0), assets["body"])

        # 3. Otros traits en orden fijo
        for trait in ["helmet", "eyes", "boots", "clothing", "gloves"]:
            if selected_traits.get(trait) in assets[trait]:
                trait_img = assets[trait][selected_traits[trait]]
                nft_img.paste(trait_img, (0, 0), trait_img)

        # ▸ Construir metadata
        rarity = "rare" if full_set_flag else "common"
        metadata["attributes"].append({"display_type": "string", "trait_type": "Rarity", "value": rarity})
        trait_display_names = {
            "boots": "Boots",
            "clothing": "Armor",
            "eyes": "Eyes",
            "gloves": "Gloves",
            "helmet": "Helmet",
            "weapon": "Weapon"
        }
        for trait in trait_keys:
            fname = selected_traits[trait]
            trait_value = fname.replace(".png", "")
            metadata["attributes"].append({
                "display_type": "string",
                "trait_type": trait_display_names[trait],
                "value": trait_value
            })
        metadata["attributes"].append({"display_type": "bool", "trait_type": "Shiny", "value": is_shiny})
        metadata["attributes"].append({"display_type": "bool", "trait_type": "Full Set", "value": full_set_flag})
        metadata["image"] = f"PRIMO #{nft_number:04d}.png"

        buf = io.BytesIO()
        nft_img.save(buf, format="PNG")
        buf.seek(0)
        image_bytes = buf.getvalue()

        return nft_img, metadata, image_bytes
    except Exception as e:
        st.error(f"Error generando el NFT #{nft_number}: {e}")
        raise

# ▸ Botón para generar NFTs
if st.button("Generar NFTs"):
    try:
        nft_images = []
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i in range(int(num_nfts)):
                nft_img, metadata, image_bytes = generate_nft(i, assets, full_set_prob, shiny_prob)
                nft_images.append(nft_img)
                img_filename = f"PRIMO_{i:04d}.png"
                zip_file.writestr(img_filename, image_bytes)
                meta_filename = f"PRIMO_{i:04d}.json"
                zip_file.writestr(meta_filename, json.dumps(metadata, indent=4))
        zip_buffer.seek(0)
        st.success(f"¡Se han generado {num_nfts} NFTs!")
        st.image(nft_images[:min(5, len(nft_images))], caption=[f"NFT {i}" for i in range(min(5, len(nft_images)))], width=150)
        st.download_button("Descargar ZIP con NFTs", data=zip_buffer, file_name="nfts.zip", mime="application/zip")
    except Exception as e:
        st.error(f"Error durante la generación de NFTs: {e}")
