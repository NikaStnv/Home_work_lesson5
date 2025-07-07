from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os


app = Flask (__name__)
app.config['SECRET_KEY'] = 'my-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now(timezone.utc).date())
    description = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'Budget {self.id} {self.date} {self.transaction_type} {self.amount}'


with app.app_context():
    db.create_all()


@app.route('/', methods=["GET"])
def index():
    today = datetime.now(timezone.utc).date()

    all_transactions = Budget.query.all()
    total_income = sum(t.amount for t in all_transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in all_transactions if t.transaction_type == 'expense')
    balance = total_income - total_expenses
    transactions_today = Budget.query.filter(db.func.date(Budget.date) == today).order_by(Budget.id.desc()).all()
    return render_template('index.html', transactions_today=transactions_today,balance=balance, today=today)


@app.route('/all', methods=["GET"])
def all_transactions():
    all_transactions = Budget.query.all()
    total_income = sum(t.amount for t in all_transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in all_transactions if t.transaction_type == 'expense')
    balance = total_income - total_expenses
    return render_template('all.html', transactions=all_transactions,balance=balance)


@app.route('/add', methods=['POST'])
def add_transaction():
    transaction_type = request.form.get('type')
    amount = float(request.form.get('amount'))
    description = request.form.get('description')

    new_transaction = Budget(transaction_type=transaction_type, amount=abs(amount),  description=description)

    try:
        db.session.add(new_transaction)
        db.session.commit()
        flash('Транзакція успішно збережена!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Транзакція не збережена!!!', 'error')
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    transaction = Budget.query.get_or_404(id)
    if request.method == 'POST':
        transaction.description = request.form['description']
        transaction.amount = float(request.form['amount'])
        transaction.transaction_type = request.form['operation_type']
        transaction.date = datetime.strptime(request.form['date'], '%Y-%m-%d')

        db.session.commit()
        flash('Транзакція успішно оновлена!', 'success')
        return redirect(url_for('all_transactions'))
    return render_template('edit.html', transaction=transaction)


@app.route('/delete/<int:id>')
def del_transaction(id):
    deleted_transaction = Budget.query.get_or_404(id)
    try:
        db.session.delete(deleted_transaction)
        db.session.commit()
        flash('Транзакція успішно видалена!', 'success')
    except Exception as e:
        db.session.rallback()
        flash('Транзакція не видалена!!!', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
