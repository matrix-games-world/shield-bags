import { initializeApp } from "https://www.gstatic.com/firebasejs/13.1.0/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  signOut
} from "https://www.gstatic.com/firebasejs/13.1.0/firebase-auth.js";
import {
  collection,
  getFirestore,
  deleteDoc,
  doc,
  getDoc,
  getDocs,
  onSnapshot,
  setDoc
} from "https://www.gstatic.com/firebasejs/13.1.0/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const productsRef = collection(db, "products");
let currentAdmin = null;
let cloudCatalogLoaded = false;

function productDocument(product) {
  const { id, ...fields } = product;
  return Object.fromEntries(
    Object.entries(fields).filter(([, value]) => value !== undefined)
  );
}

onSnapshot(productsRef, (snapshot) => {
  if (snapshot.empty && !cloudCatalogLoaded) return;
  cloudCatalogLoaded = true;
  const products = snapshot.docs.map((item) => ({ id: item.id, ...item.data() }));
  window.shieldApplyCloudProducts?.(products);
}, (error) => {
  console.error("Could not load the public product catalog:", error);
});

window.shieldAdminLogin = async (email, password) => {
  const credential = await signInWithEmailAndPassword(auth, email, password);
  const marker = await getDoc(doc(db, "admins", credential.user.uid));

  if (!marker.exists() || marker.data().role !== "admin") {
    await signOut(auth);
    throw new Error("الحساب سجّل الدخول، لكنه غير مضاف كأدمن للموقع بعد.");
  }

  currentAdmin = credential.user;
  const snapshot = await getDocs(productsRef);
  if (snapshot.empty) {
    const seedProducts = window.shieldGetProducts?.() || [];
    await Promise.all(seedProducts.map((product) =>
      setDoc(doc(db, "products", product.id), productDocument(product))
    ));
  }
  return credential.user;
};

window.shieldAdminLogout = async () => {
  currentAdmin = null;
  await signOut(auth);
};

window.shieldSaveProduct = async (product) => {
  if (!currentAdmin) throw new Error("سجّل دخول الأدمن أولًا.");
  await setDoc(doc(db, "products", product.id), productDocument(product));
};

window.shieldDeleteProduct = async (id) => {
  if (!currentAdmin) throw new Error("سجّل دخول الأدمن أولًا.");
  await deleteDoc(doc(db, "products", id));
};
