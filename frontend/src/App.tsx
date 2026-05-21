import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ProjectPage from './pages/ProjectPage'
import AnalysisPage from './pages/AnalysisPage'
import ReportPage from './pages/ReportPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/project/:id" element={<ProjectPage />} />
        <Route path="/project/:id/analysis" element={<AnalysisPage />} />
        <Route path="/project/:id/report" element={<ReportPage />} />
      </Route>
    </Routes>
  )
}