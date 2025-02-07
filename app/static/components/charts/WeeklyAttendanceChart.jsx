import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const WeeklyAttendanceChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/weekly-attendance');
        const result = await response.json();
        
        if (result.success) {
          setData(result.data);
        } else {
          setError('Failed to load attendance data');
        }
      } catch (err) {
        setError('Error fetching attendance data');
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64">
      <div className="text-gray-500">Loading attendance data...</div>
    </div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-64">
      <div className="text-red-500">{error}</div>
    </div>;
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border rounded shadow">
          <p className="font-bold">{label}</p>
          <p className="text-green-600">
            Present: {payload[0].value}% ({payload[0].payload.present_count} students)
          </p>
          <p className="text-red-600">
            Absent: {payload[1].value}% ({payload[1].payload.absent_count} students)
          </p>
          <p className="text-gray-600">
            Total: {payload[0].payload.total} students
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis 
            tickFormatter={(value) => `${value}%`}
            domain={[0, 100]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar 
            dataKey="present" 
            name="Present" 
            fill="rgb(40, 167, 69)" 
            fillOpacity={0.5}
            strokeWidth={1}
            stroke="rgb(40, 167, 69)"
          />
          <Bar 
            dataKey="absent" 
            name="Absent" 
            fill="rgb(220, 53, 69)" 
            fillOpacity={0.5}
            strokeWidth={1}
            stroke="rgb(220, 53, 69)"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default WeeklyAttendanceChart;
