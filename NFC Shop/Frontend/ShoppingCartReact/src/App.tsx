import { Routes, Route } from "react-router-dom"
import { Container } from "react-bootstrap"
import { Store } from "./pages/Store"
import { Navbar } from "./components/Navbar"
import { ShoppingCartProvider } from "./context/ShoppingCartContext"

function App() {


  return (
    <>
      <ShoppingCartProvider>
        <Navbar />
        <Container className="mb-4">
          <Routes>
            <Route path="/" element={<Store />} /> {/* Home page */}
            <Route path="/store" element={<Store />} /> {/* Store page */}
          </Routes>
        </Container>
      </ShoppingCartProvider>
    </>
  )
}

export default App
