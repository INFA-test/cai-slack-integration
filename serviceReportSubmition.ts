import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function ServiceReportForm() {
  const [id, setId] = useState("");
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!id || !file) {
      setStatus("Please provide both ID and attachment.");
      return;
    }

    const formData = new FormData();
    formData.append("id", id);
    formData.append("attachment", file);

    try {
      const response = await fetch("/api/submit-service-report", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        setStatus("Service report submitted successfully!");
        setId("");
        setFile(null);
      } else {
        setStatus("Failed to submit report.");
      }
    } catch (error) {
      setStatus("Error submitting report.");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <Card className="w-full max-w-md shadow-lg rounded-2xl p-6">
        <CardContent>
          <h2 className="text-xl font-semibold mb-4 text-center">Submit Service Report</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium">ID</label>
              <input
                type="text"
                value={id}
                onChange={(e) => setId(e.target.value)}
                className="w-full border rounded-lg p-2 mt-1"
                placeholder="Enter service ID"
              />
            </div>

            <div>
              <label className="block text-sm font-medium">Attachment</label>
              <input
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
                className="w-full border rounded-lg p-2 mt-1"
              />
            </div>

            <Button type="submit" className="w-full">Submit</Button>
          </form>

          {status && (
            <p className="mt-4 text-center text-sm text-gray-700">{status}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
