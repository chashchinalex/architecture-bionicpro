const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors({
  origin: ['http://localhost:3000']  // port React dev-server
}));

// Data Report
const reportHeader = 'Прайс Лист BionicPRO';
const columns = ['протез', 'цена'];
const rows = [
  ['нога', '1999999'],
  ['рука', '2999999'],
  ['голова', '5999999'],
  ['глаз', '6999999'],
  ['почка', '8999999']
];

function generateCsv() {
  let out = reportHeader + '\r\n';
  out += columns.join(',') + '\r\n';
  for (const r of rows) {
    out += r.join(',') + '\r\n';
  }
  return out;
}

app.get('/reports', (req, res) => {
  const filename = 'price_list_bionicpro.csv';
  res.setHeader('Content-Type', 'text/csv; charset=utf-8');
  res.setHeader('Content-Disposition', 'attachment; filename="${filename}"');
  res.send(generateCsv());
});

const PORT = 8000;
app.listen(PORT, () => {
  console.log('BionicPRO-backend listening on http://localhost:${PORT}');
});
